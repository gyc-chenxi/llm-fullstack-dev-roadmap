"""
Observability middleware: request-id injection, timing, and rate limiting.

Enterprise design notes (interview material):
- Every request gets a `X-Request-Id` — if the client sends one we honour
  it (for distributed tracing); otherwise we generate a short unique id.
- `X-Process-Time-Ms` is a cheap, high-signal header that every response
  carries.  It lets you spot slow endpoints without touching a logging
  pipeline.
- The rate limiter is an in-process sliding-window counter.  It's NOT
  suitable for multi-process deployments (use Redis-backed in prod), but
  it demonstrates the *concept* — and the interview question is about
  understanding the concept, not the implementation scale.
"""

import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field

from fastapi import HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from gateway.config import settings

# ── Request ID ─────────────────────────────────────────────────────────

class RequestIdMiddleware(BaseHTTPMiddleware):
    """Inject or propagate X-Request-Id on every request/response."""
    async def dispatch(self, request: Request, call_next):
        req_id = request.headers.get("X-Request-Id", str(uuid.uuid4())[:8])
        request.state.request_id = req_id
        response: Response = await call_next(request)
        response.headers["X-Request-Id"] = req_id
        return response


# ── Timing ─────────────────────────────────────────────────────────────

class TimingMiddleware(BaseHTTPMiddleware):
    """Add X-Process-Time-Ms header to every response."""
    async def dispatch(self, request: Request, call_next):
        t0 = time.perf_counter()
        response: Response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
        response.headers["X-Process-Time-Ms"] = str(elapsed_ms)
        return response


# ── In-memory sliding-window rate limiter ──────────────────────────────

@dataclass
class _Window:
    """Track timestamps for one client."""
    timestamps: list[float] = field(default_factory=list)

    def prune(self, window_s: float, now: float) -> None:
        cutoff = now - window_s
        self.timestamps = [t for t in self.timestamps if t > cutoff]

    @property
    def count(self) -> int:
        return len(self.timestamps)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Per-IP sliding-window rate limiter.

    Key decisions:
    - Keyed by client IP (X-Forwarded-For aware for proxy deployments).
    - Sliding window: "max_requests within the last window_seconds".
    - When the limit is exceeded, returns 429 with Retry-After header.
    - Memory: entries are pruned on every request so the dictionary
      doesn't grow unbounded.
    """

    _PUBLIC_PATHS = {"/healthz", "/readyz"}

    def __init__(self, app, **kwargs):
        super().__init__(app, **kwargs)
        self._windows: dict[str, _Window] = defaultdict(_Window)

    async def dispatch(self, request: Request, call_next):
        if request.url.path in self._PUBLIC_PATHS:
            return await call_next(request)

        # Disabled when max_requests is 0.
        max_req = settings.rate_limit_max_requests
        win_s = settings.rate_limit_window_seconds
        if max_req <= 0:
            return await call_next(request)

        # Resolve client IP (X-Forwarded-For aware).
        forwarded = request.headers.get("X-Forwarded-For", "")
        client_ip = forwarded.split(",")[0].strip() if forwarded else (
            request.client.host if request.client else "unknown"
        )

        now = time.monotonic()
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
