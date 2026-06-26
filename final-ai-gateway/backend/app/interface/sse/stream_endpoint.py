"""
SSE endpoints — stream and resume helpers.
"""

from __future__ import annotations

from app.application.use_cases.stream_chat_use_case import StreamChatUseCase
from app.application.use_cases.resume_stream_use_case import ResumeStreamUseCase


class StreamEndpointHandler:
    def __init__(
        self,
        stream_use_case: StreamChatUseCase,
    ):
        self.stream_use_case = stream_use_case

    async def handle(self, request_id: str, messages: list[dict], **kwargs):
        async for event in self.stream_use_case.execute(
            request_id=request_id,
            messages=messages,
            **kwargs,
        ):
            yield event


class ResumeEndpointHandler:
    def __init__(self, resume_use_case: ResumeStreamUseCase):
        self.resume_use_case = resume_use_case

    async def handle(self, request_id: str, last_event_id: int = 0):
        async for event in self.resume_use_case.execute(request_id, last_event_id):
            yield event
