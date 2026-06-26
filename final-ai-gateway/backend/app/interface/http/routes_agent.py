"""
Agent Routes — POST /api/v1/agent/run, GET stream, GET resume, POST cancel
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from starlette.responses import StreamingResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/agent", tags=["agent"])


@router.post("/run")
async def agent_run(request: Request):
    """Submit an agent run request."""
    return {"message": "Agent run endpoint — connect Agent Graph in app.state"}
