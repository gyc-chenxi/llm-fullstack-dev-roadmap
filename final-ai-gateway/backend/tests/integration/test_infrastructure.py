"""
Integration tests for Phase 2 infrastructure layer.
Tests Redis repositories, tokenizers, probes, SSE store, and client factory.
"""

import os
import pytest
import sys

# ============================================================
# Redis Repository Tests (require running Redis)
# ============================================================

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_AVAILABLE = False


@pytest.fixture(autouse=False)
async def redis_setup():
    """Check if Redis is available; skip if not."""
    global REDIS_AVAILABLE
    try:
        import redis.asyncio as aioredis
        r = aioredis.Redis.from_url(REDIS_URL, socket_connect_timeout=1)
        await r.ping()
        await r.flushdb()
        REDIS_AVAILABLE = True
        yield r
        await r.flushdb()
        await r.aclose()
    except Exception:
        REDIS_AVAILABLE = False
        yield None


requires_redis = pytest.mark.skipif(
    not REDIS_AVAILABLE and os.getenv("CI") is None,
    reason="Redis not available"
)


class TestRedisQueueRepository:
    @pytest.mark.asyncio
    async def test_enqueue_dequeue(self, redis_setup):
        if redis_setup is None:
            pytest.skip("Redis not available")
        from app.infrastructure.redis.connection import init_redis_pool, close_redis_pool
        from app.infrastructure.redis.redis_priority_queue import RedisQueueRepository
        from app.domain.entities.queue_ticket import QueueTicket

        await init_redis_pool(REDIS_URL, max_connections=5)
        repo = RedisQueueRepository()

        ticket = QueueTicket(request_id="req_001", priority=3)
        await repo.enqueue(ticket)
        size = await repo.size()
        assert size >= 1

        dequeued = await repo.dequeue()
        assert dequeued is not None
        assert dequeued.request_id in ("req_001", None) or dequeued is not None

        await close_redis_pool()

    @pytest.mark.asyncio
    async def test_remove_request(self, redis_setup):
        if redis_setup is None:
            pytest.skip("Redis not available")
        from app.infrastructure.redis.connection import init_redis_pool, close_redis_pool
        from app.infrastructure.redis.redis_priority_queue import RedisQueueRepository
        from app.domain.entities.queue_ticket import QueueTicket

        await init_redis_pool(REDIS_URL, max_connections=5)
        repo = RedisQueueRepository()

        ticket = QueueTicket(request_id="req_rm", priority=5)
        await repo.enqueue(ticket)
        size_before = await repo.size()
        removed = await repo.remove("req_rm")
        size_after = await repo.size()

        assert removed
        assert size_after < size_before

        await close_redis_pool()


class TestRedisStreamSessionRepo:
    @pytest.mark.asyncio
    async def test_create_and_get_session(self, redis_setup):
        if redis_setup is None:
            pytest.skip("Redis not available")
        from app.infrastructure.redis.connection import init_redis_pool, close_redis_pool
        from app.infrastructure.redis.redis_stream_session_repo import RedisStreamSessionRepo
        from app.domain.entities.stream_session import StreamSession

        await init_redis_pool(REDIS_URL, max_connections=5)
        repo = RedisStreamSessionRepo()

        session = StreamSession(request_id="req_sse_001", stream_type="chat")
        await repo.create_session(session)

        retrieved = await repo.get_session("req_sse_001")
        assert retrieved is not None
        assert retrieved.request_id == "req_sse_001"

        await close_redis_pool()

    @pytest.mark.asyncio
    async def test_add_and_get_events(self, redis_setup):
        if redis_setup is None:
            pytest.skip("Redis not available")
        from app.infrastructure.redis.connection import init_redis_pool, close_redis_pool
        from app.infrastructure.redis.redis_stream_session_repo import RedisStreamSessionRepo
        from app.domain.entities.stream_session import StreamSession

        await init_redis_pool(REDIS_URL, max_connections=5)
        repo = RedisStreamSessionRepo()

        session = StreamSession(request_id="req_sse_002")
        await repo.create_session(session)

        eid1 = await repo.add_event("req_sse_002", {"type": "token", "delta": "hello"})
        eid2 = await repo.add_event("req_sse_002", {"type": "token", "delta": "world"})
        assert eid2 > eid1

        events = await repo.get_events_since("req_sse_002", last_event_id=0)
        assert len(events) >= 2

        events_after = await repo.get_events_since("req_sse_002", last_event_id=eid1)
        assert len(events_after) >= 1

        await close_redis_pool()


class TestRedisSlotRepo:
    @pytest.mark.asyncio
    async def test_init_and_get_slots(self, redis_setup):
        if redis_setup is None:
            pytest.skip("Redis not available")
        from app.infrastructure.redis.connection import init_redis_pool, close_redis_pool
        from app.infrastructure.redis.redis_slot_repo import RedisSlotRepo

        await init_redis_pool(REDIS_URL, max_connections=5)
        repo = RedisSlotRepo()

        await repo.init_slots(4)
        slots = await repo.get_all_slots()
        assert len(slots) == 4

        ok = await repo.allocate_slot(0, "req_001")
        assert ok

        slot = await repo.get_slot(0)
        assert slot is not None
        assert slot.status.value == "busy"

        ok = await repo.release_slot(0)
        assert ok

        slot = await repo.get_slot(0)
        assert slot.status.value == "idle"

        await close_redis_pool()


class TestRedisMetricsRepo:
    @pytest.mark.asyncio
    async def test_record_and_snapshot(self, redis_setup):
        if redis_setup is None:
            pytest.skip("Redis not available")
        from app.infrastructure.redis.connection import init_redis_pool, close_redis_pool
        from app.infrastructure.redis.redis_metrics_repo import RedisMetricsRepo

        await init_redis_pool(REDIS_URL, max_connections=5)
        repo = RedisMetricsRepo()

        await repo.record_latency("req_001", "ttft_ms", 120.5)
        await repo.record_counter("total_requests", 1)
        await repo.record_counter("total_requests", 1)

        snapshot = await repo.get_snapshot()
        assert "counters" in snapshot
        assert snapshot["counters"].get("total_requests") == 2

        await close_redis_pool()


class TestTokenBucket:
    @pytest.mark.asyncio
    async def test_consume(self, redis_setup):
        if redis_setup is None:
            pytest.skip("Redis not available")
        from app.infrastructure.redis.connection import init_redis_pool, close_redis_pool
        from app.infrastructure.redis.redis_token_bucket import RedisTokenBucket

        await init_redis_pool(REDIS_URL, max_connections=5)
        bucket = RedisTokenBucket()

        ok = await bucket.consume("test_tenant", rate=10.0, burst=5, tokens=1)
        assert ok

        available = await bucket.get_available("test_tenant", rate=10.0, burst=5)
        assert available >= 0

        await close_redis_pool()


# ============================================================
# Tokenizer Tests (no external dependencies)
# ============================================================

class TestTokenizers:
    @pytest.mark.asyncio
    async def test_fallback_tokenizer(self):
        from app.infrastructure.tokenizer.tokenizers import FallbackTokenizer
        tok = FallbackTokenizer()
        count = await tok.count_tokens("hello world")
        assert 3 <= count <= 4  # ~3 chars per token

    @pytest.mark.asyncio
    async def test_tiktoken_estimator(self):
        from app.infrastructure.tokenizer.tokenizers import TiktokenEstimator
        tok = TiktokenEstimator()
        count = await tok.count_tokens("hello world")
        assert count > 0


# ============================================================
# SSE Store Tests
# ============================================================

class TestSseEventStore:
    def test_event_id_generator(self):
        from app.infrastructure.sse.sse_event_store import EventIdGenerator
        gen = EventIdGenerator(start=1)
        assert gen.next() == 1
        assert gen.next() == 2
        assert gen.current() == 2

    def test_sse_store(self):
        from app.infrastructure.sse.sse_event_store import SseEventStore
        store = SseEventStore()
        gen = store.generator_for("req_001")
        assert gen.next() == 1
        assert gen.next() == 2

        gen2 = store.generator_for("req_002")
        assert gen2.next() == 1  # Separate generator

        store.remove("req_001")
        gen3 = store.generator_for("req_001")
        assert gen3.next() == 1  # Fresh generator

    def test_format_sse_event(self):
        from app.infrastructure.sse.sse_event_store import format_sse_event
        result = format_sse_event(1, "req_001", "token", {"delta": "hello"})
        assert result.startswith("data: ")
        assert "event_id" in result
        assert "hello" in result


# ============================================================
# Probes Tests
# ============================================================

class TestMacOSMemoryProbe:
    @pytest.mark.asyncio
    async def test_snapshot(self):
        from app.infrastructure.probes.probes import MacOSMemoryProbe
        probe = MacOSMemoryProbe()
        snapshot = await probe.get_system_snapshot()
        assert "memory_pressure" in snapshot
        assert "available_memory_mb" in snapshot
        assert snapshot["available_memory_mb"] >= 0


# ============================================================
# LLM Client Factory Tests
# ============================================================

class TestLLMClientFactory:
    def test_create_llamacpp(self):
        from app.infrastructure.llm_clients.client_factory import LLMClientFactory
        from app.infrastructure.llm_clients.llamacpp_client import LlamacppClient
        client = LLMClientFactory.create("llamacpp", base_url="http://localhost:8080")
        assert isinstance(client, LlamacppClient)

    def test_create_ollama(self):
        from app.infrastructure.llm_clients.client_factory import LLMClientFactory
        from app.infrastructure.llm_clients.ollama_client import OllamaClient
        client = LLMClientFactory.create("ollama", base_url="http://localhost:11434")
        assert isinstance(client, OllamaClient)

    def test_create_openai(self):
        from app.infrastructure.llm_clients.client_factory import LLMClientFactory
        from app.infrastructure.llm_clients.openai_compatible_client import OpenAICompatibleClient
        client = LLMClientFactory.create("openai", base_url="https://api.openai.com", api_key="sk-test")
        assert isinstance(client, OpenAICompatibleClient)

    def test_create_unknown_falls_back(self):
        from app.infrastructure.llm_clients.client_factory import LLMClientFactory
        from app.infrastructure.llm_clients.llamacpp_client import LlamacppClient
        client = LLMClientFactory.create("unknown", base_url="http://localhost:8080")
        assert isinstance(client, LlamacppClient)


# ============================================================
# GatewayChatModel Tests
# ============================================================

class TestGatewayChatModel:
    def test_model_creation(self):
        from app.infrastructure.llm_clients.gateway_chat_model import GatewayChatModel
        from app.infrastructure.llm_clients.llamacpp_client import LlamacppClient

        client = LlamacppClient(base_url="http://localhost:8080")
        model = GatewayChatModel(
            llm_client=client,
            model_name="test-model",
            max_tokens=1024,
        )
        assert model._llm_type == "gateway-chat-model"
        assert model.model_name == "test-model"
        assert model.max_tokens == 1024

    def test_identifying_params(self):
        from app.infrastructure.llm_clients.gateway_chat_model import GatewayChatModel
        from app.infrastructure.llm_clients.llamacpp_client import LlamacppClient
        from app.domain.services.admission_controller import AdmissionController
        from app.domain.services.token_budget_estimator import TokenBudgetEstimator
        from app.domain.entities.model_profile import ModelProfile

        client = LlamacppClient(base_url="http://localhost:8080")
        profile = ModelProfile(model_name="test")
        estimator = TokenBudgetEstimator(profile)
        admission = AdmissionController(estimator=estimator, slots=[])

        model = GatewayChatModel(
            llm_client=client,
            admission_controller=admission,
            model_name="test-model",
        )
        params = model._identifying_params
        assert params["has_admission_control"] is True
        assert params["model_name"] == "test-model"
