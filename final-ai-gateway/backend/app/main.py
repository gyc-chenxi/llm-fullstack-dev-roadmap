"""
AI-Gateway FastAPI Application — assembles all DDD layers with startup/shutdown hooks.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import config
from app.domain.entities.model_profile import ModelProfile
from app.domain.entities.slot import Slot, SlotStatus
from app.domain.services.admission_controller import AdmissionController
from app.domain.services.slot_allocator import SlotAllocator
from app.domain.services.token_budget_estimator import TokenBudgetEstimator
from app.infrastructure.llm_clients.client_factory import LLMClientFactory
from app.infrastructure.probes.probes import MacOSMemoryProbe
from app.infrastructure.redis.connection import init_redis_pool, close_redis_pool
from app.infrastructure.redis.redis_priority_queue import RedisQueueRepository
from app.infrastructure.redis.redis_slot_repo import RedisSlotRepo
from app.infrastructure.redis.redis_metrics_repo import RedisMetricsRepo
from app.infrastructure.redis.redis_trace_repo import RedisTraceRepo
from app.infrastructure.redis.redis_stream_session_repo import RedisStreamSessionRepo
from app.infrastructure.sse.sse_event_store import SseEventStore
from app.infrastructure.tokenizer.tokenizers import FallbackTokenizer

from app.application.use_cases.submit_chat_use_case import SubmitChatUseCase
from app.application.use_cases.stream_chat_use_case import StreamChatUseCase
from app.application.use_cases.resume_stream_use_case import ResumeStreamUseCase
from app.application.use_cases.cancel_request_use_case import CancelRequestUseCase
from app.application.use_cases.dequeue_request_use_case import DequeueRequestUseCase
from app.application.orchestrators.inference_orchestrator import InferenceOrchestrator
from app.application.orchestrators.queue_worker import QueueWorker
from app.application.orchestrators.metrics_collector import MetricsCollector
from app.application.orchestrators.trace_collector import TraceCollector

from app.interface.http.routes_chat import router as chat_router
from app.interface.http.routes_metrics import router as metrics_router
from app.interface.http.routes_slots import router as slots_router
from app.interface.http.routes_trace import router as trace_router
from app.interface.http.routes_admin import router as admin_router
from app.interface.http.routes_rag import router as rag_router
from app.interface.http.routes_agent import router as agent_router
from app.interface.http.routes_benchmark import router as benchmark_router
from app.interface.middlewares.request_id_middleware import RequestIdMiddleware
from app.interface.middlewares.error_boundary_middleware import ErrorBoundaryMiddleware

logging.basicConfig(
    level=getattr(logging, config.get("app.log_level", "INFO")),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle for the gateway."""
    logger.info("=" * 60)
    logger.info("AI-Gateway v1.0.0 starting...")
    logger.info("=" * 60)

    # --- Redis ---
    redis_url = config.redis_url
    logger.info("Connecting to Redis: %s", redis_url)
    await init_redis_pool(redis_url, max_connections=50)

    # --- Repositories ---
    queue_repo = RedisQueueRepository()
    slot_repo = RedisSlotRepo()
    metrics_repo = RedisMetricsRepo()
    trace_repo = RedisTraceRepo()
    stream_session_repo = RedisStreamSessionRepo()
    sse_store = SseEventStore()

    # --- Model Profile ---
    model_configs = config.get("model.models", [])
    default_model = model_configs[0] if model_configs else {
        "name": "qwen2.5:7b",
        "context_length": 8192,
        "max_slots": 4,
        "num_layers": 28,
        "num_kv_heads": 4,
        "head_dim": 128,
        "dtype_bytes": 2,
    }
    profile = ModelProfile(
        model_name=default_model["name"],
        model_path=default_model.get("url", ""),
        context_length=default_model.get("context_length", 8192),
        max_slots=default_model.get("max_slots", 4),
        num_layers=default_model.get("num_layers", 28),
        num_kv_heads=default_model.get("num_kv_heads", 4),
        head_dim=default_model.get("head_dim", 128),
        dtype_bytes=default_model.get("dtype_bytes", 2),
    )

    # --- Domain Services ---
    estimator = TokenBudgetEstimator(profile)
    slots = [Slot(slot_id=i, status=SlotStatus.IDLE) for i in range(profile.max_slots)]
    slot_allocator = SlotAllocator(slots=slots)
    admission_controller = AdmissionController(estimator=estimator, slots=slots)

    # --- Infrastructure ---
    llm_client = LLMClientFactory.create(
        backend=default_model.get("backend", "llamacpp"),
        base_url=default_model.get("url", "http://127.0.0.1:8080"),
    )
    tokenizer = FallbackTokenizer()
    system_probe = MacOSMemoryProbe()

    # --- Use Cases ---
    submit_use_case = SubmitChatUseCase(
        llm_client=llm_client,
        tokenizer=tokenizer,
        admission_controller=admission_controller,
        slot_allocator=slot_allocator,
        queue_repo=queue_repo,
        slot_repo=slot_repo,
        trace_repo=trace_repo,
        stream_session_repo=stream_session_repo,
        sse_store=sse_store,
    )
    stream_use_case = StreamChatUseCase(
        llm_client=llm_client,
        slot_repo=slot_repo,
        trace_repo=trace_repo,
        stream_session_repo=stream_session_repo,
        sse_store=sse_store,
    )
    resume_use_case = ResumeStreamUseCase(
        stream_session_repo=stream_session_repo,
        trace_repo=trace_repo,
        sse_store=sse_store,
    )
    cancel_use_case = CancelRequestUseCase(
        queue_repo=queue_repo,
        slot_repo=slot_repo,
        trace_repo=trace_repo,
        stream_session_repo=stream_session_repo,
    )
    dequeue_use_case = DequeueRequestUseCase(
        queue_repo=queue_repo,
        slot_allocator=slot_allocator,
        slot_repo=slot_repo,
        stream_session_repo=stream_session_repo,
    )

    # --- Orchestrators ---
    inference_orchestrator = InferenceOrchestrator(
        submit_use_case=submit_use_case,
        stream_use_case=stream_use_case,
        resume_use_case=resume_use_case,
        cancel_use_case=cancel_use_case,
    )
    queue_worker = QueueWorker(dequeue_use_case=dequeue_use_case, poll_interval_sec=0.5)
    metrics_collector = MetricsCollector(
        metrics_repo=metrics_repo,
        slot_repo=slot_repo,
        trace_repo=trace_repo,
        system_probe=system_probe,
        collection_interval_sec=10.0,
    )
    trace_collector = TraceCollector(trace_repo=trace_repo)

    # --- Attach to app state ---
    app.state.llm_client = llm_client
    app.state.tokenizer = tokenizer
    app.state.profile = profile
    app.state.admission_controller = admission_controller
    app.state.slot_allocator = slot_allocator
    app.state.slot_repo = slot_repo
    app.state.queue_repo = queue_repo
    app.state.metrics_repo = metrics_repo
    app.state.trace_repo = trace_repo
    app.state.stream_session_repo = stream_session_repo
    app.state.sse_store = sse_store
    app.state.inference_orchestrator = inference_orchestrator
    app.state.queue_worker = queue_worker
    app.state.metrics_collector = metrics_collector
    app.state.trace_collector = trace_collector

    # --- Initialize slots in Redis ---
    await slot_repo.init_slots(profile.max_slots)

    # --- Start background workers ---
    await queue_worker.start()
    await metrics_collector.start()

    logger.info("AI-Gateway ready — %d slots, %s model", profile.max_slots, profile.model_name)

    yield

    # --- Shutdown ---
    logger.info("Shutting down...")
    await queue_worker.stop()
    await metrics_collector.stop()
    await llm_client.close()
    await close_redis_pool()
    logger.info("AI-Gateway stopped.")


app = FastAPI(
    title="AI-Gateway",
    version="1.0.0",
    description="Enterprise Lightweight LLM / RAG / Agent Serving Governance Gateway",
    lifespan=lifespan,
)

# --- Middlewares ---
app.add_middleware(ErrorBoundaryMiddleware)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routers ---
app.include_router(chat_router)
app.include_router(metrics_router)
app.include_router(slots_router)
app.include_router(trace_router)
app.include_router(admin_router)
app.include_router(rag_router)
app.include_router(agent_router)
app.include_router(benchmark_router)


@app.get("/")
async def root():
    return {
        "service": "AI-Gateway",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "chat": "/api/v1/chat",
            "metrics": "/api/v1/metrics/snapshot",
            "slots": "/api/v1/slots",
            "trace": "/api/v1/trace",
            "admin": "/api/v1/admin/health",
        },
    }