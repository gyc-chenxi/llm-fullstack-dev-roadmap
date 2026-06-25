"""
健康检查路由
-----------
提供 /healthz 和 /readyz 端点，供 k8s 存活探针(liveness)和就绪探针(readiness)使用。
两个端点逻辑相同：检查上游 llama-server 是否可访问。

设计说明：
  - 即使上游不可用，健康检查端点本身也返回 200（status 标记为 degraded）。
    避免 k8s 因上游抖动而不断重启 Gateway Pod。
  - 端点免认证（注册在 ApiKeyMiddleware._PUBLIC_PATHS 中）。
"""

from fastapi import APIRouter, Request
from gateway.schemas import HealthResponse
from gateway.config import settings

router = APIRouter(tags=["health"])


@router.get("/healthz", response_model=HealthResponse)
async def healthz(request: Request):
    """
    存活探针（Liveness Probe）。
    返回 Gateway 自身是否存活以及上游状态。
    """
    ok, detail = await request.app.state.llamacpp.health()
    return HealthResponse(
        status="ok" if ok else "degraded",
        upstream=settings.llamacpp_base_url,
        detail=detail,
    )


@router.get("/readyz", response_model=HealthResponse)
async def readyz(request: Request):
    """
    就绪探针（Readiness Probe）。
    逻辑与 healthz 相同，k8s 在两个维度分别配置时可使用不同端点。
    """
    ok, detail = await request.app.state.llamacpp.health()
    return HealthResponse(
        status="ok" if ok else "degraded",
        upstream=settings.llamacpp_base_url,
        detail=detail,
    )