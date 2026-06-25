"""
集成测试（轻量版）：健康端点、中间件行为、校验错误
==================================================

测试策略：
  使用 httpx.ASGITransport 在进程中模拟 HTTP 请求穿越 FastAPI 中间件栈，
  无需启动 uvicorn 或依赖真实上游 llama-server。

  LlamaCppClient 被 AsyncMock 替换，所有上游调用返回预设值。

数据流：
  httpx.AsyncClient (ASGITransport)
    → FastAPI app (全部中间件栈: Timing → RequestId → RateLimit → ApiKey → CORS)
    → Route Handler
      → app.state.llamacpp (AsyncMock, 不发起真实 HTTP 请求)
    → 响应返回

运行： python -m pytest tests/ -v
"""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from gateway.app import app


@pytest.fixture
async def client():
    """
    In-process 异步测试客户端。

    创建方式：
      1. ASGITransport 接管 FastAPI app，模拟 ASGI 协议通信
      2. 用 AsyncMock 替换 LlamaCppClient，避免连接真实 upstream
      3. 由于 ASGITransport 不触发 lifespan，手动注入 app.state.llamacpp

    返回：
      httpx.AsyncClient — 可直接调用 app 内任意路由，不涉及网络 IO
    """
    transport = ASGITransport(app=app)

    # Mock LlamaCppClient —— 隔离上游依赖，使测试专注 Gateway 自身逻辑
    mock_llamacpp = AsyncMock()
    mock_llamacpp.health.return_value = (True, "mock: llama-server ready")

    # ASGITransport bypasses lifespan，需手动注入
    app.state.llamacpp = mock_llamacpp

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestHealthEndpoints:
    """健康检查端点测试（/healthz, /readyz）—— k8s 探针兼容性验证。"""

    async def test_healthz_returns_200(self, client: AsyncClient):
        """正常情况：上游可用 → status=ok，返回 200。"""
        resp = await client.get("/healthz")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert "upstream" in body

    async def test_readyz_returns_200(self, client: AsyncClient):
        """就绪探针：逻辑与 healthz 相同，确保独立端点正常工作。"""
        resp = await client.get("/readyz")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"

    async def test_healthz_returns_degraded_when_upstream_down(self, client: AsyncClient):
        """
        上游不可用时：
          - healthz 本身仍返回 200（Gateway 自身存活）
          - status 标记为 degraded（供监控系统告警）
          k8s 不会因此重启 Pod，避免上游抖动引起级联重启。
        """
        app.state.llamacpp.health.return_value = (False, "connection refused")
        resp = await client.get("/healthz")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "degraded"


class TestMetricsEndpoint:
    """运营指标端点测试（/gateway/metrics）。"""

    async def test_metrics_returns_200(self, client: AsyncClient):
        """指标端点应始终返回 200，包含 uptime 和累计请求数。"""
        resp = await client.get("/gateway/metrics")
        assert resp.status_code == 200
        body = resp.json()
        assert "uptime_seconds" in body
        assert "requests_total" in body


class TestValidationErrors:
    """Pydantic 请求校验失败场景测试。"""

    async def test_missing_body_returns_422(self, client: AsyncClient):
        """
        空请求体 → 422 + VALIDATION_ERROR。
        验证 validation_exception_handler 正确序列化字段级错误详情。
        """
        resp = await client.post("/v1/chat/completions", json={})
        assert resp.status_code == 422
        body = resp.json()
        assert body["code"] == "VALIDATION_ERROR"
        assert "details" in body

    async def test_no_user_message_returns_422(self, client: AsyncClient):
        """
        缺少 user 角色消息 → 422。
        验证 ChatCompletionRequest.validate_messages 的自定义校验逻辑。
        """
        resp = await client.post("/v1/chat/completions", json={
            "messages": [{"role": "system", "content": "no user here"}],
        })
        assert resp.status_code == 422
        body = resp.json()
        assert body["code"] == "VALIDATION_ERROR"


class TestMiddlewareHeaders:
    """中间件注入的 HTTP 响应头测试。"""

    async def test_response_has_request_id(self, client: AsyncClient):
        """
        验证 RequestIdMiddleware：
        - 响应中应始终包含 X-Request-Id 头
        - 客户端未传入时自动生成（≥8 字符）
        """
        resp = await client.get("/healthz")
        assert "x-request-id" in resp.headers
        assert len(resp.headers["x-request-id"]) >= 8

    async def test_response_has_timing_header(self, client: AsyncClient):
        """
        验证 TimingMiddleware：
        - 响应中包含 X-Process-Time-Ms 头
        - 值为非负浮点数（毫秒级精度）
        """
        resp = await client.get("/healthz")
        assert "x-process-time-ms" in resp.headers
        assert float(resp.headers["x-process-time-ms"]) >= 0.0

    async def test_request_id_propagates_from_header(self, client: AsyncClient):
        """
        验证 X-Request-Id 透传：
          客户端传入自定义 ID → 响应中应返回相同值
          （用于分布式追踪中串联 Gateway 与客户端的请求链路）
        """
        resp = await client.get("/healthz", headers={"X-Request-Id": "my-custom-id-123"})
        assert resp.headers["x-request-id"] == "my-custom-id-123"