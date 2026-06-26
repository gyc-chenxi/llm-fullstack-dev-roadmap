"""
Stream chat use case — executes the actual LLM streaming with governance.
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import AsyncIterator

from app.domain.entities.inference_request import RequestStatus
from app.domain.entities.stream_session import StreamStatus
from app.domain.entities.trace_run import TraceRun
from app.domain.ports.llm_client import LLMClientPort
from app.domain.ports.slot_repository import SlotRepositoryPort
from app.domain.ports.trace_repository import TraceRepositoryPort
from app.domain.services.output_guard import OutputGuard
from app.domain.services.circuit_breaker import CircuitBreaker
from app.domain.services.stream_health_detector import StreamHealthDetector
from app.infrastructure.redis.redis_stream_session_repo import RedisStreamSessionRepo
from app.infrastructure.sse.sse_event_store import EventIdGenerator, SseEventStore, format_sse_event

logger = logging.getLogger(__name__)


class StreamChatUseCase:
    def __init__(
        self,
        llm_client: LLMClientPort,
        slot_repo: SlotRepositoryPort,
        trace_repo: TraceRepositoryPort,
        stream_session_repo: RedisStreamSessionRepo,
        sse_store: SseEventStore,
        output_guard: OutputGuard = None,
        circuit_breaker: CircuitBreaker = None,
    ):
        self.llm_client = llm_client
        self.slot_repo = slot_repo
        self.trace_repo = trace_repo
        self.stream_session_repo = stream_session_repo
        self.sse_store = sse_store
        self.output_guard = output_guard or OutputGuard()
        self.circuit_breaker = circuit_breaker

    async def execute(
        self,
        request_id: str,
        messages: list[dict],
        model: str = "qwen2.5-7b-instruct-q4_k_m",
        max_tokens: int = 2048,
        temperature: float = 0.7,
        slot_id: int = 0,
    ) -> AsyncIterator[str]:
        event_gen = self.sse_store.generator_for(request_id)
        health = StreamHealthDetector()
        self.output_guard.reset()

        start_time = time.monotonic()
        first_token_time = None
        total_tokens = 0
        full_text = ""

        # Send meta event
        meta_event = format_sse_event(
            event_gen.next(), request_id, "meta",
            {"model": model, "max_tokens": max_tokens}
        )
        yield meta_event
        await self.stream_session_repo.add_event(request_id, {
            "type": "meta", "model": model, "max_tokens": max_tokens,
        })

        try:
            async for event in self.llm_client.chat_completion(
                messages=messages,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True,
            ):
                if event.get("type") == "done":
                    break

                if event.get("type") == "token":
                    token = event.get("content", "")
                    if not token:
                        continue

                    if first_token_time is None:
                        first_token_time = time.monotonic()

                    # Output guard check
                    fault = self.output_guard.check(token)
                    if fault:
                        warning_event = format_sse_event(
                            event_gen.next(), request_id, "warning",
                            {"message": fault.message, "fault_type": fault.fault_type.value}
                        )
                        yield warning_event
                        await self.stream_session_repo.add_event(request_id, {
                            "type": "warning", "message": fault.message,
                        })

                    full_text += token
                    total_tokens += 1
                    health.record_event()

                    sse_data = {"delta": token}
                    sse_str = format_sse_event(event_gen.next(), request_id, "token", sse_data)
                    yield sse_str
                    await self.stream_session_repo.add_event(request_id, {
                        "type": "token", "delta": token,
                    })

                    if health.needs_heartbeat:
                        yield ": heartbeat\n\n"

        except Exception as e:
            logger.error("Stream error for %s: %s", request_id, e)
            error_event = format_sse_event(
                event_gen.next(), request_id, "error",
                {"message": str(e)}
            )
            yield error_event
            await self.stream_session_repo.add_event(request_id, {
                "type": "error", "message": str(e),
            })
            await self.stream_session_repo.update_status(request_id, StreamStatus.FAILED, str(e))

        finally:
            end_time = time.monotonic()
            ttft = (first_token_time - start_time) * 1000 if first_token_time else 0
            total_latency = (end_time - start_time) * 1000
            tpot = ttft / total_tokens if total_tokens > 0 else 0

            # Done event
            done_event = format_sse_event(
                event_gen.next(), request_id, "done",
                {
                    "total_tokens": total_tokens,
                    "ttft_ms": round(ttft, 2),
                    "total_latency_ms": round(total_latency, 2),
                }
            )
            yield done_event
            await self.stream_session_repo.add_event(request_id, {
                "type": "done", "total_tokens": total_tokens,
            })
            await self.stream_session_repo.update_status(request_id, StreamStatus.DONE)

            # Release slot
            await self.slot_repo.release_slot(slot_id)

            # Update trace
            trace = await self.trace_repo.get(request_id)
            if trace is None:
                trace = TraceRun(request_id=request_id, run_type="chat")
            trace.completion_tokens = total_tokens
            trace.ttft_ms = ttft
            trace.tpot_ms = tpot
            trace.latency_ms = total_latency
            trace.final_status = "completed"
            await self.trace_repo.save(trace)

            self.sse_store.remove(request_id)