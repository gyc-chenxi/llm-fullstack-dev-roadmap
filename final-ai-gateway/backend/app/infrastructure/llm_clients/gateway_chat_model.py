"""
GatewayChatModel — LangChain BaseChatModel adapter.
All LLM calls from LangChain/LangGraph go through Gateway governance
(AdmissionController, SlotAllocator, OutputGuard, CircuitBreaker) via this adapter.
"""

from __future__ import annotations

import logging
from typing import Any, AsyncIterator, Iterator, Optional

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import ConfigDict

from app.domain.ports.llm_client import LLMClientPort
from app.domain.services.admission_controller import AdmissionController
from app.domain.services.output_guard import OutputGuard
from app.domain.services.circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)


class GatewayChatModel(BaseChatModel):
    """
    LangChain ChatModel adapter that routes all model calls through the AI-Gateway
    governance layer (admission control, slots, output guard, circuit breaker).

    Usage in LangChain:
        model = GatewayChatModel(client=llamacpp_client, admission=controller)
        chain = prompt | model | output_parser
    """

    llm_client: LLMClientPort
    admission_controller: Optional[AdmissionController] = None
    output_guard: Optional[OutputGuard] = None
    circuit_breaker: Optional[CircuitBreaker] = None
    model_name: str = "qwen2.5-7b-instruct-q4_k_m"
    max_tokens: int = 2048
    temperature: float = 0.7
    gateway_stream: bool = True

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def _llm_type(self) -> str:
        return "gateway-chat-model"

    @property
    def _identifying_params(self) -> dict[str, Any]:
        return {
            "model_name": self.model_name,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "has_admission_control": self.admission_controller is not None,
            "has_output_guard": self.output_guard is not None,
            "has_circuit_breaker": self.circuit_breaker is not None,
        }

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: Optional[list[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs,
    ) -> ChatResult:
        import asyncio

        full_text = ""
        async def _collect():
            nonlocal full_text
            async for chunk in self._astream(messages, stop=stop, **kwargs):
                full_text += chunk.content
        asyncio.get_event_loop().run_until_complete(_collect())
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=full_text))])

    async def _agenerate(
        self,
        messages: list[BaseMessage],
        stop: Optional[list[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs,
    ) -> ChatResult:
        full_text = ""
        async for chunk in self._astream(messages, stop=stop, **kwargs):
            full_text += chunk.content
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=full_text))])

    def _stream(
        self,
        messages: list[BaseMessage],
        stop: Optional[list[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs,
    ) -> Iterator[ChatGeneration]:
        import asyncio

        async def _adapt():
            for item in _collect():
                yield item

        async def _collect():
            gen = self._astream(messages, stop=stop, **kwargs)
            async for chunk in gen:
                yield chunk

        queue = asyncio.Queue()
        async def _run():
            async for chunk in _collect():
                await queue.put(chunk)
            await queue.put(None)

        loop = asyncio.get_event_loop()
        task = loop.create_task(_run())

        while True:
            try:
                chunk = loop.run_until_complete(queue.get())
                if chunk is None:
                    break
                yield chunk
            except Exception:
                break

    async def _astream(
        self,
        messages: list[BaseMessage],
        stop: Optional[list[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs,
    ) -> AsyncIterator[ChatGeneration]:
        prompt_list = []
        for m in messages:
            role = "user" if m.type == "human" else "assistant" if m.type == "ai" else "system"
            prompt_list.append({"role": role, "content": self._extract_content(m)})

        allowed = True
        if self.admission_controller:
            text = " ".join(self._extract_content(m) for m in messages)
            prompt_tokens = len(text) // 3
            decision = self.admission_controller.evaluate(
                prompt_tokens=prompt_tokens,
                max_new_tokens=kwargs.get("max_tokens", self.max_tokens),
            )
            if decision.decision.value not in ("admit", "degrade"):
                yield ChatGeneration(message=AIMessage(
                    content=f"[Gateway: {decision.decision.value.upper()} - {decision.reason}]"))
                return

        full_text = ""
        guard = self.output_guard or OutputGuard()
        guard.reset()

        async def _stream():
            nonlocal full_text
            async for event in self.llm_client.chat_completion(
                messages=prompt_list,
                model=kwargs.get("model", self.model_name),
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                temperature=kwargs.get("temperature", self.temperature),
                stream=self.gateway_stream,
                stop=stop,
            ):
                if event.get("type") == "done":
                    break
                if event.get("type") == "token":
                    token = event.get("content", "")
                    if token:
                        full_text += token
                        yield ChatGeneration(message=AIMessage(content=token))
                    if guard.check(token):
                        logger.warning("Output guard triggered, stopping generation")
                        break

        try:
            if self.circuit_breaker:
                async for chunk in self.circuit_breaker.call(lambda: _stream()):
                    yield chunk
            else:
                async for chunk in _stream():
                    yield chunk
        except Exception as e:
            logger.error("GatewayChatModel stream error: %s", e)
            yield ChatGeneration(message=AIMessage(content=f"\n[Gateway Error: {e}]"))

    @staticmethod
    def _extract_content(message: BaseMessage) -> str:
        if isinstance(message.content, str):
            return message.content
        if isinstance(message.content, list):
            text_parts = [item["text"] for item in message.content if isinstance(item, dict) and item.get("type") == "text"]
            return " ".join(text_parts)
        return str(message.content)
