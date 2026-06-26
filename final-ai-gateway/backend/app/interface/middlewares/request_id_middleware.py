"""
Request ID middleware — assigns a unique ID to every incoming request.
"""

from __future__ import annotations

import uuid
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", f"req_{uuid.uuid4().hex[:12]}")
        request.state.request_id = request_id
        request.state.start_time = time.monotonic()

        response: Response = await call_next(request)

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{time.monotonic() - request.state.start_time:.3f}s"
        return response
