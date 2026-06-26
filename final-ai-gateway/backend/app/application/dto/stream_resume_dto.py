"""
Stream resume DTO.
"""

from __future__ import annotations

from pydantic import BaseModel


class StreamResumeDTO(BaseModel):
    request_id: str
    last_event_id: int = 0