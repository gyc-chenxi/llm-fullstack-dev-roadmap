"""
DeepSeek LLM 包装器
======================

通过 OpenAI-compatible SDK 调用 DeepSeek API (chat/completions 端点)，
实现 LlamaIndex CustomLLM 接口。

数据流：
  prompt/messages → OpenAI SDK → POST https://api.deepseek.com/v1/chat/completions
  → ChatCompletion(response.choices[0].message.content) → CompletionResponse

为什么自己实现 CustomLLM 而不是用 LangChain 的 ChatDeepSeek：
  - LlamaIndex 的 Settings.llm 需要实现 CustomLLM 接口
  - 直接调用 chat/completions API（非旧版 completions），避免 API 兼容问题
  - DeepSeek 默认使用 Chat Completion API，旧版 Completions 有限制

配置方式：
  Settings.llm = DeepSeekLLM(
      model="deepseek-chat",
      api_key="sk-...",        # 可选，默认读 DEEPSEEK_API_KEY
      temperature=0.0,
      max_tokens=1024,
  )
"""

from typing import Any, Dict, Optional, Sequence

from llama_index.core.base.llms.types import (
    ChatMessage,
    ChatResponse,
    CompletionResponse,
    LLMMetadata,
)
from llama_index.core.llms import CustomLLM
from llama_index.core.llms.callbacks import llm_completion_callback, llm_chat_callback
from openai import OpenAI


class DeepSeekLLM(CustomLLM):
    """基于 OpenAI SDK 的 DeepSeek CustomLLM。

    通过 model_dump() 序列化响应元数据（raw field），便于调试和日志记录。
    """

    model: str = "deepseek-chat"
    api_key: str = ""
    api_base: str = "https://api.deepseek.com"
    temperature: float = 0.0
    max_tokens: int = 1024
    context_window: int = 128000
    num_output: int = 8192

    def __init__(
        self,
        model: str = "deepseek-chat",
        api_key: Optional[str] = None,
        api_base: str = "https://api.deepseek.com",
        temperature: float = 0.0,
        max_tokens: int = 1024,
        **kwargs,
    ):
        import os

        super().__init__(
            model=model,
            api_key=api_key or os.getenv("DEEPSEEK_API_KEY", ""),
            api_base=api_base,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

    @property
    def metadata(self) -> LLMMetadata:
        return LLMMetadata(
            context_window=self.context_window,
            num_output=self.num_output,
            model_name=self.model,
            is_chat_model=True,
        )

    def _get_client(self) -> OpenAI:
        """获取 OpenAI 客户端（base_url 指向 DeepSeek）。"""
        import os

        return OpenAI(
            api_key=self.api_key,
            base_url=self.api_base,
        )

    def _messages_from_prompt(self, prompt: str) -> list:
        """将 prompt 字符串转为 chat messages 格式。"""
        return [{"role": "user", "content": prompt}]

    @llm_completion_callback()
    def complete(self, prompt: str, **kwargs) -> CompletionResponse:
        """同步完成请求（prompt → chat/completions → response.text）。"""
        client = self._get_client()
        messages = self._messages_from_prompt(prompt)

        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
        )

        text = response.choices[0].message.content or ""
        return CompletionResponse(text=text)

    @llm_completion_callback()
    def stream_complete(self, prompt: str, **kwargs):
        """流式完成请求（generator of CompletionResponse with delta）。"""
        client = self._get_client()
        messages = self._messages_from_prompt(prompt)

        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
            stream=True,
        )

        def gen():
            for chunk in response:
                delta = chunk.choices[0].delta
                if delta.content:
                    yield CompletionResponse(text=delta.content, delta=delta.content)

        return gen()

    @llm_chat_callback()
    def chat(self, messages: Sequence[ChatMessage], **kwargs) -> ChatResponse:
        """Chat 消息接口（LlamaIndex 内部调用的主路径）。"""
        client = self._get_client()
        api_messages = [
            {"role": m.role.value if hasattr(m.role, 'value') else str(m.role),
             "content": str(m.content or "")}
            for m in messages
        ]

        response = client.chat.completions.create(
            model=self.model,
            messages=api_messages,
            temperature=self.temperature,
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
        )

        text = response.choices[0].message.content or ""
        return ChatResponse(
            message=ChatMessage(role="assistant", content=text),
            raw=response.model_dump(),  # 保留原始响应用于调试
        )
