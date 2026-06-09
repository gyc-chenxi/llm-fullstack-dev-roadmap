"""
Unified error codes & exception handlers.

Design principle (enterprise interview answer):
- Every error gets a stable `code` that the frontend/monitoring can key on.
- HTTP status codes alone are ambiguous — a 502 could be "upstream down" or
  "upstream timed out reading the response".  The `code` string disambiguates.
- All handlers return JSON, never HTML — this is an API gateway, not a CMS.
"""

from fastapi import Request
from fastapi.responses import ORJSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

# ── Error code catalogue ──────────────────────────────────────────────
# Keep this flat — no nesting, no inheritance.  Just a registry of codes
# that a frontend or SRE can grep for in logs / Datadog / Grafana.

ERROR_CODES = {
    # 4xx — caller fault
    "VALIDATION_ERROR":       "Request body or query parameter failed schema validation.",
    "AUTH_MISSING":           "No API key provided in X-API-Key header.",
    "AUTH_INVALID":           "The provided API key is not valid.",
    "RATE_LIMIT_EXCEEDED":    "Too many requests.  Retry after the Retry-After seconds.",
    # 5xx — upstream / gateway fault
    "UPSTREAM_TIMEOUT":       "The upstream llama-server did not respond in time.",
    "UPSTREAM_CONNECT_ERROR": "Could not connect to the upstream llama-server.",
    "UPSTREAM_HTTP_ERROR":    "The upstream returned an unexpected HTTP error.",
    "UPSTREAM_INVALID_JSON":  "The upstream returned a malformed JSON body.",
    "INTERNAL_ERROR":         "An unexpected internal error occurred.",
}

# ── Exception handlers ─────────────────────────────────────────────────

async def validation_exception_handler(
    request: Request, exc: RequestValidationError,
) -> ORJSONResponse:
    """Pydantic validation failures → structured 422."""
    details = []
    for err in exc.errors():
        details.append({
            "loc": list(err.get("loc", [])),
            "msg": err.get("msg", ""),
            "type": err.get("type", ""),
        })
    return ORJSONResponse(
        status_code=422,
        content={
            "code": "VALIDATION_ERROR",
            "message": ERROR_CODES["VALIDATION_ERROR"],
            "details": details,
        },
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException,
) -> ORJSONResponse:
    """Catch-all for HTTPException raised anywhere in the app."""
    # Map common status codes to our error code catalogue.
    code_map: dict[int, str] = {
        401: "AUTH_MISSING",
        403: "AUTH_INVALID",
        429: "RATE_LIMIT_EXCEEDED",
        502: "UPSTREAM_CONNECT_ERROR",
        504: "UPSTREAM_TIMEOUT",
    }
    code = code_map.get(exc.status_code, "INTERNAL_ERROR")
    return ORJSONResponse(
        status_code=exc.status_code,
        content={
            "code": code,
            "message": str(exc.detail) if exc.detail else ERROR_CODES.get(code, ""),
        },
    )


async def generic_exception_handler(
    request: Request, exc: Exception,
) -> ORJSONResponse:
    """Last-resort handler for unhandled exceptions."""
    return ORJSONResponse(
        status_code=500,
        content={
            "code": "INTERNAL_ERROR",
            "message": ERROR_CODES["INTERNAL_ERROR"],
        },
    )
