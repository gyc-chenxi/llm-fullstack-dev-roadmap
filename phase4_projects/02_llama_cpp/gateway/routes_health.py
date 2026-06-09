from fastapi import APIRouter, Request
from gateway.schemas import HealthResponse
from gateway.config import settings

router = APIRouter(tags=["health"])


@router.get("/healthz", response_model=HealthResponse)
async def healthz(request: Request):
    ok, detail = await request.app.state.llamacpp.health()
    return HealthResponse(
        status="ok" if ok else "degraded",
        upstream=settings.llamacpp_base_url,
        detail=detail,
    )


@router.get("/readyz", response_model=HealthResponse)
async def readyz(request: Request):
    ok, detail = await request.app.state.llamacpp.health()
    return HealthResponse(
        status="ok" if ok else "degraded",
        upstream=settings.llamacpp_base_url,
        detail=detail,
    )