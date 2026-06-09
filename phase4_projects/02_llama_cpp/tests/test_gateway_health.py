"""Integration-lite tests for health endpoints and middleware.

Run:  python -m pytest tests/ -v
Uses in-process ASGI transport — no uvicorn needed.
"""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from gateway.app import app


@pytest.fixture
async def client():
    """In-process async test client with mocked llama.cpp upstream."""
    transport = ASGITransport(app=app)

    # Mock the LlamaCppClient so we don't need a real llama-server.
    mock_llamacpp = AsyncMock()
    mock_llamacpp.health.return_value = (True, "mock: llama-server ready")

    # ASGITransport bypasses lifespan, so we inject state manually.
    app.state.llamacpp = mock_llamacpp

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestHealthEndpoints:
    async def test_healthz_returns_200(self, client: AsyncClient):
        resp = await client.get("/healthz")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert "upstream" in body

    async def test_readyz_returns_200(self, client: AsyncClient):
        resp = await client.get("/readyz")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"

    async def test_healthz_returns_degraded_when_upstream_down(self, client: AsyncClient):
        app.state.llamacpp.health.return_value = (False, "connection refused")
        resp = await client.get("/healthz")
        assert resp.status_code == 200  # healthz itself doesn't fail
        body = resp.json()
        assert body["status"] == "degraded"


class TestMetricsEndpoint:
    async def test_metrics_returns_200(self, client: AsyncClient):
        resp = await client.get("/gateway/metrics")
        assert resp.status_code == 200
        body = resp.json()
        assert "uptime_seconds" in body
        assert "requests_total" in body


class TestValidationErrors:
    async def test_missing_body_returns_422(self, client: AsyncClient):
        resp = await client.post("/v1/chat/completions", json={})
        assert resp.status_code == 422
        body = resp.json()
        assert body["code"] == "VALIDATION_ERROR"
        assert "details" in body

    async def test_no_user_message_returns_422(self, client: AsyncClient):
        resp = await client.post("/v1/chat/completions", json={
            "messages": [{"role": "system", "content": "no user here"}],
        })
        assert resp.status_code == 422
        body = resp.json()
        assert body["code"] == "VALIDATION_ERROR"


class TestMiddlewareHeaders:
    async def test_response_has_request_id(self, client: AsyncClient):
        resp = await client.get("/healthz")
        assert "x-request-id" in resp.headers
        assert len(resp.headers["x-request-id"]) >= 8

    async def test_response_has_timing_header(self, client: AsyncClient):
        resp = await client.get("/healthz")
        assert "x-process-time-ms" in resp.headers
        assert float(resp.headers["x-process-time-ms"]) >= 0.0

    async def test_request_id_propagates_from_header(self, client: AsyncClient):
        resp = await client.get("/healthz", headers={"X-Request-Id": "my-custom-id-123"})
        assert resp.headers["x-request-id"] == "my-custom-id-123"
