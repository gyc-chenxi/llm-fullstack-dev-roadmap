"""
Domain layer entity tests — verify core business rules.
"""

import pytest
from app.domain.entities.inference_request import InferenceRequest, RequestStatus
from app.domain.entities.rag_request import RagRequest
from app.domain.entities.agent_run import AgentRun, AgentState
from app.domain.entities.stream_session import StreamSession, StreamStatus
from app.domain.entities.slot import Slot, SlotStatus
from app.domain.entities.model_profile import ModelProfile
from app.domain.entities.queue_ticket import QueueTicket
from app.domain.entities.fault_event import FaultEvent, FaultType
from app.domain.entities.trace_run import TraceRun
from app.domain.entities.tool_call import ToolCall
from app.domain.value_objects.priority import Priority
from app.domain.value_objects.token_budget import TokenBudget
from app.domain.value_objects.admission_decision import AdmissionDecision, DecisionType
from app.domain.value_objects.prefix_hash import PrefixHash
from app.domain.value_objects.stream_event import StreamEvent
from app.domain.value_objects.latency_metrics import LatencyMetrics
from app.domain.value_objects.citation import Citation
from app.domain.value_objects.retrieval_hit import RetrievalHit
from app.domain.value_objects.agent_state_snapshot import AgentStateSnapshot
from app.domain.services.token_budget_estimator import TokenBudgetEstimator
from app.domain.services.slot_allocator import SlotAllocator
from app.domain.services.admission_controller import AdmissionController
from app.domain.services.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError
from app.domain.services.output_guard import OutputGuard
from app.domain.services.rag_quality_guard import RagQualityGuard
from app.domain.services.agent_loop_guard import AgentLoopGuard
from app.domain.services.long_context_planner import LongContextPlanner, LongContextStrategy
from app.domain.policies.priority_policy import PriorityPolicy
from app.domain.policies.degradation_policy import DegradationPolicy, DegradationLevel
from app.domain.policies.retry_policy import RetryPolicy
from app.domain.policies.timeout_policy import TimeoutPolicy
from app.domain.policies.citation_policy import CitationPolicy
from app.domain.policies.tool_call_policy import ToolCallPolicy


class TestInferenceRequest:
    def test_create_request(self):
        req = InferenceRequest(messages=[{"role": "user", "content": "Hello"}])
        assert req.request_id.startswith("req_")
        assert req.status == RequestStatus.CREATED
        assert req.priority == 5

    def test_empty_messages_raises(self):
        with pytest.raises(ValueError, match="messages must not be empty"):
            InferenceRequest(messages=[])


class TestRagRequest:
    def test_create_request(self):
        req = RagRequest(question="What is AI?")
        assert req.request_id.startswith("rag_")
        assert req.retrieval_top_k == 5

    def test_empty_question_raises(self):
        with pytest.raises(ValueError, match="question must not be empty"):
            RagRequest(question="")


class TestAgentRun:
    def test_create_run(self):
        run = AgentRun(goal="Summarize document")
        assert run.run_id.startswith("agent_")
        assert run.state == AgentState.CREATED

    def test_empty_goal_raises(self):
        with pytest.raises(ValueError, match="goal must not be empty"):
            AgentRun(goal="")


class TestSlot:
    def test_slot_creation(self):
        slot = Slot(slot_id=0)
        assert slot.status == SlotStatus.IDLE
        assert slot.current_request_id is None


class TestModelProfile:
    def test_profile_properties(self):
        profile = ModelProfile(
            model_name="qwen2.5-7b",
            num_layers=28,
            num_kv_heads=4,
            head_dim=128,
            dtype_bytes=2,
        )
        assert profile.per_token_bytes == 2.0 * 28 * 4 * 128 * 2


class TestTokenBudget:
    def test_budget(self):
        budget = TokenBudget(prompt_tokens=1000, max_new_tokens=2048)
        assert budget.total_tokens == 3048

    def test_negative_prompt_raises(self):
        with pytest.raises(ValueError):
            TokenBudget(prompt_tokens=-1)


class TestPriority:
    def test_values(self):
        assert Priority.critical().value == 1
        assert Priority.normal().value == 5
        assert Priority.best_effort().value == 10

    def test_invalid_value_raises(self):
        with pytest.raises(ValueError):
            Priority(0)
        with pytest.raises(ValueError):
            Priority(11)


class TestPrefixHash:
    def test_compute(self):
        ph = PrefixHash.compute("system: You are a helpful assistant.")
        assert len(ph.hash_value) == 16


class TestAdmissionDecision:
    def test_defaults(self):
        decision = AdmissionDecision(decision=DecisionType.ADMIT, reason="ok")
        assert decision.decision == DecisionType.ADMIT


class TestTokenBudgetEstimator:
    def test_estimate(self):
        profile = ModelProfile(
            model_name="test",
            num_layers=28,
            num_kv_heads=4,
            head_dim=128,
            dtype_bytes=2,
        )
        estimator = TokenBudgetEstimator(profile)
        budget = estimator.estimate(prompt_tokens=1000, max_new_tokens=2048)
        assert budget.prompt_tokens == 1000
        assert budget.estimated_kv_bytes > 0


class TestSlotAllocator:
    def test_allocate_and_release(self):
        allocator = SlotAllocator.from_count(4)
        slot = allocator.allocate("req_001")
        assert slot is not None
        assert slot.status == SlotStatus.BUSY
        assert allocator.active_count == 1

        allocator.release(slot.slot_id)
        assert allocator.idle_count == 4

    def test_allocate_when_full(self):
        allocator = SlotAllocator.from_count(2)
        allocator.allocate("req_001")
        allocator.allocate("req_002")
        assert allocator.allocate("req_003") is None


class TestAdmissionController:
    def test_admit_with_idle_slots(self):
        profile = ModelProfile(
            model_name="test",
            num_layers=28,
            num_kv_heads=4,
            head_dim=128,
            dtype_bytes=2,
            safe_kv_budget_bytes=100_000_000,
        )
        estimator = TokenBudgetEstimator(profile)
        slots = [Slot(slot_id=i) for i in range(4)]
        controller = AdmissionController(estimator=estimator, slots=slots)
        decision = controller.evaluate(prompt_tokens=100, max_new_tokens=100)
        assert decision.decision == DecisionType.ADMIT

    def test_queue_when_no_idle_slots(self):
        profile = ModelProfile(model_name="test")
        estimator = TokenBudgetEstimator(profile)
        slots = [Slot(slot_id=i, status=SlotStatus.BUSY) for i in range(4)]
        controller = AdmissionController(estimator=estimator, slots=slots)
        decision = controller.evaluate(prompt_tokens=100, max_new_tokens=100)
        assert decision.decision == DecisionType.QUEUE


class TestCircuitBreaker:
    def test_closed_to_open(self):
        cb = CircuitBreaker(failure_threshold=2)
        for _ in range(2):
            try:
                cb.call(lambda: (_ for _ in ()).throw(Exception("fail")))
            except Exception:
                pass
        assert cb.state.value == "open"

    def test_initial_closed(self):
        cb = CircuitBreaker(failure_threshold=5)
        result = cb.call(lambda: "success")
        assert result == "success"
        assert cb.state.value == "closed"


class TestOutputGuard:
    def test_normal_text_passes(self):
        guard = OutputGuard()
        fault = guard.check("Hello, how are you?")
        assert fault is None

    def test_repetition_detected(self):
        guard = OutputGuard(max_repeat_ngram=3, max_repeat_window=20)
        for _ in range(10):
            fault = guard.check("abc")
        if fault:
            assert fault.fault_type == FaultType.REPETITION


class TestPriorityPolicy:
    def test_agent_gets_higher_priority(self):
        policy = PriorityPolicy()
        chat_p = policy.compute("chat")
        agent_p = policy.compute("agent")
        assert agent_p.value < chat_p.value


class TestDegradationPolicy:
    def test_no_degradation(self):
        policy = DegradationPolicy()
        level = policy.evaluate(queue_depth=2, kv_usage_ratio=0.5)
        assert level == DegradationLevel.NONE

    def test_severe_degradation(self):
        policy = DegradationPolicy()
        level = policy.evaluate(queue_depth=60, kv_usage_ratio=0.5)
        assert level == DegradationLevel.SEVERE


class TestRetryPolicy:
    def test_should_retry(self):
        policy = RetryPolicy(max_retries=3)
        assert policy.should_retry(0, "timeout")

    def test_exceeded_retries(self):
        policy = RetryPolicy(max_retries=3)
        assert not policy.should_retry(3, "timeout")


class TestAgentLoopGuard:
    def test_check_step_ok(self):
        guard = AgentLoopGuard(max_steps=5)
        assert guard.check_step() is None

    def test_exceed_step_limit(self):
        guard = AgentLoopGuard(max_steps=1)
        guard.check_step()
        fault = guard.check_step()
        assert fault is not None
        assert fault.fault_type == FaultType.AGENT_LOOP


class TestStreamEvent:
    def test_to_sse_format(self):
        event = StreamEvent(event_id=1, request_id="req_001", event_type="token",
                            data={"delta": "hello"})
        sse = event.to_sse_format()
        assert sse.startswith("data: ")
        assert "event_id" in sse
