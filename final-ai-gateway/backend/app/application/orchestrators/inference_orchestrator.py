"""
Inference orchestrator — coordinates the full chat pipeline end-to-end.
"""

from __future__ import annotations

import asyncio
import logging
from typing import AsyncIterator

from app.application.use_cases.cancel_request_use_case import CancelRequestUseCase
from app.application.use_cases.resume_stream_use_case import ResumeStreamUseCase
from app.application.use_cases.stream_chat_use_case import StreamChatUseCase
from app.application.use_cases.submit_chat_use_case import SubmitChatUseCase

logger = logging.getLogger(__name__)


class InferenceOrchestrator:
    def __init__(
        self,
        submit_use_case: SubmitChatUseCase,
        stream_use_case: StreamChatUseCase,
        resume_use_case: ResumeStreamUseCase,
        cancel_use_case: CancelRequestUseCase,
    ):
        self.submit_use_case = submit_use_case
        self.stream_use_case = stream_use_case
        self.resume_use_case = resume_use_case
        self.cancel_use_case = cancel_use_case

    async def submit(
        self,
        messages: list[dict],
        model: str = "qwen2.5-7b-instruct-q4_k_m",
        max_tokens: int = 2048,
        temperature: float = 0.7,
        stream: bool = True,
        priority: int = 5,
        tenant_id: str = "default",
    ) -> dict:
        return await self.submit_use_case.execute(
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=stream,
            priority=priority,
            tenant_id=tenant_id,
        )

    async def stream(
        self,
        request_id: str,
        messages: list[dict],
        model: str = "qwen2.5-7b-instruct-q4_k_m",
        max_tokens: int = 2048,
        temperature: float = 0.7,
        slot_id: int = 0,
    ) -> AsyncIterator[str]:
        async for event in self.stream_use_case.execute(
            request_id=request_id,
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            slot_id=slot_id,
        ):
            yield event

    async def resume(self, request_id: str, last_event_id: int = 0) -> AsyncIterator[str]:
        async for event in self.resume_use_case.execute(request_id, last_event_id):
            yield event

    async def cancel(self, request_id: str) -> dict:
        return await self.cancel_use_case.execute(request_id)
