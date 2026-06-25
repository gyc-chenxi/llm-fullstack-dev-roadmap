"""
API Key 认证中间件
-----------------
企业级网关认证模式：检查请求头 X-API-Key 是否匹配配置值。

面试要点（架构思考）：
  - 这是*网关级别*的 API Key 检查，不是 OAuth2/JWT 完整流程。
    生产环境可以替换为 Auth0 / Clerk / Kong 等，无需修改任何 route 代码
    ——这正是 FastAPI middleware 模式的威力。
  - Key 从环境变量加载（config.Settings），支持不重启容器旋转密钥。
    在 k8s 中应挂载为 Secret。
  - 当 GATEWAY_API_KEY 为空（默认）时关闭认证，保持本地开发零摩擦。
    生产环境必须设置该环境变量。

数据流：
  请求进入 → ApiKeyMiddleware.dispatch()
    ├─ 路径在 {/healthz, /readyz} → 放行（k8s 探针需免认证）
    ├─ GATEWAY_API_KEY 为空     → 放行（本地开发模式）
    ├─ X-API-Key 头部缺失       → 401 AUTH_MISSING
    ├─ X-API-Key 值不匹配       → 403 AUTH_INVALID
    └─ 校验通过                → 放行到下一层中间件/路由
"""

import secrets

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware

from gateway.config import settings


class ApiKeyMiddleware(BaseHTTPMiddleware):
    """
    网关 API Key 认证中间件。

    使用 secrets.compare_digest 进行常数时间比较，
    避免时序侧信道攻击（timing side-channel）。
    """

    _PUBLIC_PATHS = {"/healthz", "/readyz"}

    async def dispatch(self, request: Request, call_next):
        # k8s 存活/就绪探针路径免认证
        if request.url.path in self._PUBLIC_PATHS:
            return await call_next(request)

        # 配置为空 → 本地开发模式，免认证
        if not settings.gateway_api_key:
            return await call_next(request)

        # 校验 X-API-Key
        provided = request.headers.get("X-API-Key", "")
        if not provided:
            raise HTTPException(status_code=401, detail="Missing X-API-Key header")
        # secrets.compare_digest：常数时间比较，防止时序攻击
        if not secrets.compare_digest(provided, settings.gateway_api_key):
            raise HTTPException(status_code=403, detail="Invalid API key")

        return await call_next(request)
