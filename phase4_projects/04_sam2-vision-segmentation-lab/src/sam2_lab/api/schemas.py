"""
API 数据模型 (Pydantic Schemas)
------------------------------
定义 FastAPI 接口的请求与响应数据结构。
"""
from __future__ import annotations

from pydantic import BaseModel, Field

# ── 健康检查 ──────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str = Field(..., example="ok")
    device: str = Field(..., example="mps")
    model: str = Field(..., example="sam2.1_hiera_tiny")


# ── Point 分割 ────────────────────────────────────────────

class SegmentPointRequest(BaseModel):
    x: int = Field(..., ge=0, description="目标点 X 坐标", example=400)
    y: int = Field(..., ge=0, description="目标点 Y 坐标", example=300)
    label: int = Field(default=1, ge=0, le=1, description="1=前景, 0=背景")


class SegmentPointResponse(BaseModel):
    status: str = "success"
    best_score: float = Field(..., example=0.95)
    point: list[int] = Field(..., example=[400, 300])
    mask_area_px: int = Field(..., example=50000, description="分割 mask 的像素面积")


# ── Box 分割 ──────────────────────────────────────────────

class SegmentBoxRequest(BaseModel):
    x1: int = Field(..., ge=0, description="框左上角 X", example=100)
    y1: int = Field(..., ge=0, description="框左上角 Y", example=80)
    x2: int = Field(..., ge=0, description="框右下角 X", example=700)
    y2: int = Field(..., ge=0, description="框右下角 Y", example=600)


class SegmentBoxResponse(BaseModel):
    status: str = "success"
    best_score: float = Field(..., example=0.92)
    box: list[int] = Field(..., example=[100, 80, 700, 600])
    mask_area_px: int = Field(..., example=50000)


# ── 错误响应 ──────────────────────────────────────────────

class ErrorResponse(BaseModel):
    status: str = "error"
    detail: str = Field(..., example="无法读取图片")
