"""
RAG Routes — POST /api/v1/rag/query, GET stream, POST evaluate
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from starlette.responses import StreamingResponse

from app.application.dto.rag_request_dto import ChatResponseDTO

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/rag", tags=["rag"])


@router.post("/query")
async def rag_query(request: Request):
    """Submit a RAG query."""
    return {"message": "RAG query endpoint — connect RAG runtime in app.state"}
