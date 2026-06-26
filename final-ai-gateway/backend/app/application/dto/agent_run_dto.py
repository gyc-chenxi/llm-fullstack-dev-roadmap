"""
Agent run DTO.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class AgentRunDTO(BaseModel):
    goal: str = Field(..., min_length=1)
    agent_type: str = "rag_agent"
    max_steps: int = Field(default=20, ge=1, le=100)
    tenant_id: str = "default"


class AgentRunResponseDTO(BaseModel):
    run_id: str
    status: str
    stream_url: Optional[str] = None
    trace_id: Optional[str] = None