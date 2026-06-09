"""
Simple API Key authentication middleware.

Enterprise context (what to say in an interview):
- This is a *gateway-level* API key check, not a full OAuth2/JWT flow.
  In production you'd swap this out for a proper auth service (Auth0, Clerk,
  Kong, etc.) without changing any route code — that's the power of
  FastAPI's middleware/dependency-injection pattern.
- The key is loaded from config (env), so it can be rotated without a
  redeploy.  In k8s you'd mount it as a Secret.
- When GATEWAY_API_KEY is empty (the default), auth is **disabled** so
  local dev stays frictionless.  In production the env var MUST be set.
"""

import secrets

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware

from gateway.config import settings


class ApiKeyMiddleware(BaseHTTPMiddleware):
    """
    If GATEWAY_API_KEY is set, require `X-API-Key: <key>` on every request
    except health endpoints (which are intentionally public for k8s probes).

    Uses `secrets.compare_digest` to avoid timing side-channels — a
    small detail that shows you've thought about security beyond "if a == b".
    """

    _PUBLIC_PATHS = {"/healthz", "/readyz"}

    async def dispatch(self, request: Request, call_next):
        # Health endpoints are always public (k8s liveness/readiness probes).
        if request.url.path in self._PUBLIC_PATHS:
            return await call_next(request)

        # Auth disabled — local dev mode.
        if not settings.gateway_api_key:
            return await call_next(request)

        provided = request.headers.get("X-API-Key", "")
        if not provided:
            raise HTTPException(status_code=401, detail="Missing X-API-Key header")
        if not secrets.compare_digest(provided, settings.gateway_api_key):
            raise HTTPException(status_code=403, detail="Invalid API key")

        return await call_next(request)
