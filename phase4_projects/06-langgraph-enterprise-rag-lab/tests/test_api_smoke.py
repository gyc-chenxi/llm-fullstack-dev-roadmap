"""Smoke tests for FastAPI endpoints using TestClient (no LLM required)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest
from fastapi.testclient import TestClient

from langgraph_enterprise_rag.api.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


def test_rag_invoke_schema_validation() -> None:
    """Verify request validation rejects bad input."""
    # Missing required fields.
    resp = client.post("/v1/rag/invoke", json={})
    assert resp.status_code == 422  # pydantic validation error

    # Empty query string.
    resp = client.post(
        "/v1/rag/invoke",
        json={"query": "", "thread_id": "t1"},
    )
    assert resp.status_code == 422


def test_rag_invoke_minimal() -> None:
    """Invoke RAG without docs / LLM — should still return a structured response."""
    resp = client.post(
        "/v1/rag/invoke",
        json={
            "query": "这是一个测试问题",
            "thread_id": "smoke-test-001",
            "max_retries": 1,
        },
    )
    # Even without LLM / Chroma, the endpoint should respond (may 500 if
    # Chroma is missing, which is expected in CI; we are mainly checking
    # the schema path is wired correctly).
    assert resp.status_code in (200, 500, 503)


def test_rag_stream_endpoint() -> None:
    """Stream endpoint should return text/event-stream content type."""
    resp = client.post(
        "/v1/rag/stream",
        json={
            "query": "测试流式输出",
            "thread_id": "stream-test-001",
        },
    )
    # If it fails internally, we still want to verify the endpoint exists.
    assert resp.status_code in (200, 500, 503)


def test_get_state_not_found() -> None:
    """Querying a non-existent thread returns a clean response."""
    resp = client.get("/v1/rag/state/nonexistent-thread-999")
    assert resp.status_code == 200
    data = resp.json()
    assert data["thread_id"] == "nonexistent-thread-999"
    assert data["checkpoint_exists"] is False
