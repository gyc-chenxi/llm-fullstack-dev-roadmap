from __future__ import annotations

from pydantic import BaseModel, Field


class VisionRequest(BaseModel):
    image_path: str = Field(..., description="Local image path")
    question: str = Field(..., description="User question")
    system_prompt: str | None = Field(None, description="Optional system prompt")


class VisionResponse(BaseModel):
    answer: str
    model: str
    device: str