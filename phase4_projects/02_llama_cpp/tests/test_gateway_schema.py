"""Unit tests for Gateway Pydantic schemas.

Run:  python -m pytest tests/ -v
"""

import pytest
from pydantic import ValidationError

from gateway.schemas import ChatMessage, ChatCompletionRequest, HealthResponse


class TestChatMessage:
    def test_valid_message(self):
        m = ChatMessage(role="user", content="hello")
        assert m.role == "user"
        assert m.content == "hello"

    def test_invalid_role(self):
        with pytest.raises(ValidationError):
            ChatMessage(role="invalid_role", content="x")  # type: ignore[arg-type]

    def test_empty_content_allowed(self):
        """Empty content is technically valid (e.g., tool calls with no text)."""
        m = ChatMessage(role="assistant", content="")
        assert m.content == ""


class TestChatCompletionRequest:
    def test_minimal_valid(self):
        req = ChatCompletionRequest(
            messages=[ChatMessage(role="user", content="hi")],
        )
        assert req.model is None
        assert req.stream is False
        assert req.temperature == 0.2

    def test_no_user_message_rejected(self):
        with pytest.raises(ValidationError, match="user"):
            ChatCompletionRequest(
                messages=[ChatMessage(role="system", content="system only")],
            )

    def test_empty_messages_rejected(self):
        with pytest.raises(ValidationError):
            ChatCompletionRequest(messages=[])

    def test_to_upstream_payload_uses_default_model(self):
        req = ChatCompletionRequest(
            model=None,
            messages=[ChatMessage(role="user", content="hi")],
        )
        payload = req.to_upstream_payload(default_model="test-model")
        assert payload["model"] == "test-model"

    def test_to_upstream_payload_uses_explicit_model(self):
        req = ChatCompletionRequest(
            model="custom-model",
            messages=[ChatMessage(role="user", content="hi")],
        )
        payload = req.to_upstream_payload(default_model="test-model")
        assert payload["model"] == "custom-model"

    def test_extra_body_is_merged(self):
        req = ChatCompletionRequest(
            messages=[ChatMessage(role="user", content="hi")],
            extra_body={"grammar": 'root ::= "yes" | "no"'},
        )
        payload = req.to_upstream_payload(default_model="m")
        assert payload["grammar"] == 'root ::= "yes" | "no"'

    def test_temperature_bounds(self):
        with pytest.raises(ValidationError):
            ChatCompletionRequest(
                messages=[ChatMessage(role="user", content="hi")],
                temperature=3.0,
            )

    def test_max_tokens_bounds(self):
        with pytest.raises(ValidationError):
            ChatCompletionRequest(
                messages=[ChatMessage(role="user", content="hi")],
                max_tokens=99999,
            )


class TestHealthResponse:
    def test_ok(self):
        h = HealthResponse(status="ok", upstream="http://x", detail="ready")
        assert h.status == "ok"

    def test_degraded(self):
        h = HealthResponse(status="degraded", upstream="http://x", detail="oops")
        assert h.status == "degraded"

    def test_detail_nullable(self):
        h = HealthResponse(status="ok", upstream="http://x")
        assert h.detail is None
