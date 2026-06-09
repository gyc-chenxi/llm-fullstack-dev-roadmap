"""健康检查路由"""

import time
from fastapi import APIRouter, Request

router = APIRouter(tags=["Health"])

_start_time = time.time()


@router.get("/healthz")
async def healthz():
    """存活检查 — 服务是否在运行"""
    return {"status": "ok", "uptime_seconds": int(time.time() - _start_time)}


@router.get("/readyz")
async def readyz(request: Request):
    """就绪检查 — 上游 Provider 是否可达"""
    try:
        client = request.app.state.http_client
        # 简单检查 OpenAI API 可达性
        resp = await client.get(
            "https://api.openai.com/v1/models",
            headers={"Authorization": "Bearer sk-test"},
            timeout=5,
        )
        # 401 说明 API 可达（只是没传合法 key）
        upstream_ok = resp.status_code in (200, 401)
    except Exception:
        upstream_ok = False

    status_code = 200 if upstream_ok else 503
    return {"status": "ok" if upstream_ok else "degraded", "upstream_reachable": upstream_ok}


@router.get("/metrics")
async def metrics():
    """基础指标"""
    return {
        "uptime_seconds": int(time.time() - _start_time),
        "version": "2.0.0",
    }
