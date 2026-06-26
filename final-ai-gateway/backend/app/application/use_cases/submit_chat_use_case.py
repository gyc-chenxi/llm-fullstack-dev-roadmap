"""
Submit chat use case — orchestrates the full admission pipeline for a chat request.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from app.domain.entities.inference_request import InferenceRequest, RequestStatus
from app.domain.entities.queue_ticket import QueueTicket
from app.domain.entities.stream_session import StreamSession
from app.domain.entities.trace_run import TraceRun
from app.domain.ports.llm_client import LLMClientPort
from app.domain.ports.queue_repository import QueueRepositoryPort
from app.domain.ports.slot_repository import SlotRepositoryPort
from app.domain.ports.tokenizer_port import TokenizerPort
from app.domain.ports.trace_repository import TraceRepositoryPort
from app.domain.services.admission_controller import AdmissionController
from app.domain.services.slot_allocator import SlotAllocator
from app.domain.services.token_budget_estimator import TokenBudgetEstimator
from app.domain.value_objects.admission_decision import DecisionType
from app.infrastructure.redis.redis_stream_session_repo import RedisStreamSessionRepo
from app.infrastructure.sse.sse_event_store import SseEventStore

logger = logging.getLogger(__name__)


class SubmitChatUseCase:
    def __init__(
        self,
        llm_client: LLMClientPort,
        tokenizer: TokenizerPort,
        admission_controller: AdmissionController,
        slot_allocator: SlotAllocator,
        queue_repo: QueueRepositoryPort,
        slot_repo: SlotRepositoryPort,
        trace_repo: TraceRepositoryPort,
        stream_session_repo: RedisStreamSessionRepo,
        sse_store: SseEventStore,
    ):
        self.llm_client = llm_client
        self.tokenizer = tokenizer
        self.admission_controller = admission_controller
        self.slot_allocator = slot_allocator
        self.queue_repo = queue_repo
        self.slot_repo = slot_repo
        self.trace_repo = trace_repo
        self.stream_session_repo = stream_session_repo
        self.sse_store = sse_store

    async def execute(
        self,
        messages: list[dict],
        model: str = "qwen2.5-7b-instruct-q4_k_m",
        max_tokens: int = 2048,
        temperature: float = 0.7,
        stream: bool = True,
        priority: int = 5,
        tenant_id: str = "default",
    ) -> dict:
        request = InferenceRequest(
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=stream,
            priority=priority,
            tenant_id=tenant_id,
        )

        prompt_text = " ".join(m.get("content", "") for m in messages)
        prompt_tokens = await self.tokenizer.count_tokens(prompt_text)
        request.estimated_prompt_tokens = prompt_tokens
        request.estimated_total_tokens = prompt_tokens + max_tokens

        decision = self.admission_controller.evaluate(
            prompt_tokens=prompt_tokens,
            max_new_tokens=max_tokens,
        )

        trace = TraceRun(
            request_id=request.request_id,
            run_type="chat",
            prompt_tokens=prompt_tokens,
            model_backend=model,
            created_at=datetime.now(timezone.utc),
        )

        if decision.decision == DecisionType.ADMIT:
            slot = self.slot_allocator.allocate(request.request_id)
            if slot is None:
                decision.decision = DecisionType.QUEUE
                decision.reason = "allocation failed — queuing"
            else:
                request.slot_id = slot.slot_id
                request.status = RequestStatus.ADMITTED
                await self.slot_repo.allocate_slot(slot.slot_id, request.request_id)

        if decision.decision == DecisionType.QUEUE:
            request.status = RequestStatus.QUEUED
            ticket = QueueTicket(
                request_id=request.request_id,
                priority=priority,
            )
            await self.queue_repo.enqueue(ticket)
            trace.final_status = "queued"
        elif decision.decision == DecisionType.ADMIT:
            request.status = RequestStatus.ADMITTED
            trace.final_status = "admitted"
            session = StreamSession(
                request_id=request.request_id,
                stream_type="chat",
            )
            await self.stream_session_repo.create_session(session)

        await self.trace_repo.save(trace)

        return {
            "request_id": request.request_id,
            "status": request.status.value,
            "stream_url": f"/api/v1/chat/{request.request_id}/stream" if stream else None,
            "trace_id": trace.trace_id,
            "queue_position": await self.queue_repo.size() if decision.decision == DecisionType.QUEUE else 0,
            "estimated_wait_ms": decision.estimated_wait_ms,
            "admission_decision": decision.decision.value,
            "slot_id": request.slot_id,
        }