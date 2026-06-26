"""
Error boundary middleware — catches unhandled exceptions and returns structured errors.
"""

from __future__ import annotations

import logging
import traceback

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class ErrorBoundaryMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as e:
            logger.error("Unhandled error: %s\n%s", e, traceback.format_exc())
            return JSONResponse(
                status_code=500,
                content={
                    "error": "internal_server_error",
                    "message": str(e),
                    "request_id": getattr(request.state, "request_id", "unknown"),
                },
            )
