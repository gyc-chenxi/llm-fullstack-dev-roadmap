"""
FastAPI application factory — llama.cpp AI Gateway.

Middleware stack (order matters — outer runs first):
  1. Timing         — X-Process-Time-Ms on every response
  2. RequestId      — X-Request-Id injection / propagation
  3. RateLimit      — per-IP sliding-window (optional, config-driven)
  4. ApiKey         — X-API-Key header check (optional, config-driven)
  5. CORS           — browser preflight / origin allowlist

Enterprise note: middleware is added OUTERMOST-first.  When a request
arrives it passes through 1→2→3→4→5→route; the response unwinds in
reverse.  Timing wraps everything so we measure the full stack.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from gateway.config import settings
from gateway.errors import (
    validation_exception_handler,
    http_exception_handler,
    generic_exception_handler,
)
from gateway.llamacpp_client import LlamaCppClient
from gateway.middleware import (
    TimingMiddleware,
    RequestIdMiddleware,
    RateLimitMiddleware,
)
from gateway.auth import ApiKeyMiddleware
from gateway.routes_chat import router as chat_router
from gateway.routes_health import router as health_router
from gateway.routes_metrics import router as metrics_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle: create httpx connection pool at startup, release at shutdown.
    One AsyncClient per process = connection reuse across all requests.
    """
    app.state.llamacpp = LlamaCppClient()
    yield
    await app.state.llamacpp.close()


app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    lifespan=lifespan,
    description="Local AI Gateway — OpenAI-compatible proxy to llama.cpp with rate limiting, API key auth, and observability.",
)

# ── Exception handlers (register before routes) ────────────────────────
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# ── Middleware (outermost first) ────────────────────────────────────────
app.add_middleware(TimingMiddleware)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(ApiKeyMiddleware)

# CORS — last middleware (closest to route), so it handles preflight first.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ─────────────────────────────────────────────────────────────
app.include_router(health_router)
app.include_router(metrics_router)
app.include_router(chat_router)
