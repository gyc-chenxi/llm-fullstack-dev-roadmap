"""
可观测性中间件：请求追踪、响应计时、速率限制
------------------------------------------

中间件执行顺序（FastAPI 中 outer 最先执行）：
  1. TimingMiddleware       ← 最外层，包裹整个请求链路计时
  2. RequestIdMiddleware    ← 注入/透传 X-Request-Id
  3. RateLimitMiddleware    ← 每 IP 滑动窗口限流（可选）
  4. ApiKeyMiddleware       ← API Key 认证（可选）
  ↓
  路由处理 → 响应反向逐层返回

设计要点（面试素材）：
  - X-Request-Id：客户端传入则透传（分布式追踪），否则自动生成 8 位 UUID
  - X-Process-Time-Ms：每条响应携带，无须额外日志管道即可发现慢端点
  - 速率限制：进程内滑动窗口，多进程需改用 Redis 实现
"""

import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field

from fastapi import HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from gateway.config import settings

# ── 请求追踪 ──

class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    注入或透传 X-Request-Id 头。
    - 客户端传入 → 透传（用于分布式追踪串联）
    - 客户端未传 → 自动生成 8 位 UUID
    """
    async def dispatch(self, request: Request, call_next):
        req_id = request.headers.get("X-Request-Id", str(uuid.uuid4())[:8])
        request.state.request_id = req_id
        response: Response = await call_next(request)
        response.headers["X-Request-Id"] = req_id
        return response


# ── 响应计时 ──

class TimingMiddleware(BaseHTTPMiddleware):
    """为每条响应添加 X-Process-Time-Ms 头（最外层，测量全链路延迟）。"""
    async def dispatch(self, request: Request, call_next):
        t0 = time.perf_counter()
        response: Response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
        response.headers["X-Process-Time-Ms"] = str(elapsed_ms)
        return response


# ── 进程内滑动窗口限流器 ──

@dataclass
class _Window:
    """单个客户端的滑动窗口状态。"""
    timestamps: list[float] = field(default_factory=list)

    def prune(self, window_s: float, now: float) -> None:
        """移除窗口之外的时间戳（过期裁剪）。"""
        cutoff = now - window_s
        self.timestamps = [t for t in self.timestamps if t > cutoff]

    @property
    def count(self) -> int:
        return len(self.timestamps)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    每 IP 滑动窗口速率限制器。

    算法：
      - 以客户端 IP（感知 X-Forwarded-For）为 key
      - 维护最近 window_seconds 秒内的时间戳列表
      - 每次请求时：prune → 判断是否超过上限 → 未超过则追加时间戳
      - 超过上限返回 429 + Retry-After 头部

    缺陷：
      - 进程内存储，多进程/多实例部署时需改为 Redis sorted set
      - 内存占用随请求数线性增长，但每次请求 prune 自动回收
    """

    _PUBLIC_PATHS = {"/healthz", "/readyz"}  # 健康检查不参与限流

    def __init__(self, app, **kwargs):
        super().__init__(app, **kwargs)
        self._windows: dict[str, _Window] = defaultdict(_Window)

    async def dispatch(self, request: Request, call_next):
        # 健康检查端点不限流（k8s 探针会高频访问）
        if request.url.path in self._PUBLIC_PATHS:
            return await call_next(request)

        # rate_limit_max_requests ≤ 0 表示关闭限流
        max_req = settings.rate_limit_max_requests
        win_s = settings.rate_limit_window_seconds
        if max_req <= 0:
            return await call_next(request)

        # 解析客户端 IP（支持反向代理场景的 X-Forwarded-For）
        forwarded = request.headers.get("X-Forwarded-For", "")
        client_ip = forwarded.split(",")[0].strip() if forwarded else (
            request.client.host if request.client else "unknown"
        )

        now = time.monotonic()  # 不受系统时间调整影响
        win = self._windows[client_ip]
        win.prune(win_s, now)

        if win.count >= max_req:
            retry_after = int(win_s)
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Retry after {retry_after}s.",
                headers={"Retry-After": str(retry_after)},
            )

        win.timestamps.append(now)
        return await call_next(request)
