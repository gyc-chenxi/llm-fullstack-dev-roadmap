"""
API 路由定义
-----------
将 FastAPI 端点处理逻辑从 server.py 中分离，
便于单独测试和维护。
"""
from __future__ import annotations

import cv2
import numpy as np
from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import JSONResponse

from sam2_lab.api.schemas import (
    HealthResponse,
    SegmentBoxResponse,
    SegmentPointResponse,
)

router = APIRouter()

# 全局预测器引用（由 server.py 在启动时注入）
_predictor = None
_device = "cpu"


def set_predictor(predictor, device: str) -> None:
    """注入 SAM2 预测器实例（在 lifespan 中调用）。"""
    global _predictor, _device
    _predictor = predictor
    _device = device


def get_predictor():
    """获取当前的 SAM2 预测器实例。"""
    if _predictor is None:
        raise RuntimeError("SAM2 模型尚未加载")
    return _predictor


def _read_image(file: UploadFile) -> np.ndarray:
    """从 UploadFile 读取并解码为 RGB 格式的 numpy 数组。"""
    contents = file.file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img_bgr is None:
        raise ValueError("无法解码图片数据")
    return cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """服务健康检查 + 设备信息。"""
    return HealthResponse(
        status="ok",
        device=_device,
        model="sam2.1_hiera_tiny",
    )


@router.post("/segment/point", response_model=SegmentPointResponse)
async def segment_point(
    image: UploadFile = File(...),  # noqa: B008
    x: int = Form(...),  # noqa: B008
    y: int = Form(...),  # noqa: B008
    label: int = Form(1),  # noqa: B008
):
    predictor = get_predictor()

    try:
        img_rgb = _read_image(image)
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "detail": str(e)},
        )

    predictor.set_image(img_rgb)
    input_point = np.array([[x, y]])
    input_label = np.array([label])

    masks, scores, _ = predictor.predict(
        point_coords=input_point,
        point_labels=input_label,
        multimask_output=True,
    )

    best_idx = np.argmax(scores)
    best_score = float(scores[best_idx])
    mask_area = int(masks[best_idx].sum())

    return SegmentPointResponse(
        best_score=best_score,
        point=[x, y],
        mask_area_px=mask_area,
    )


@router.post("/segment/box", response_model=SegmentBoxResponse)
async def segment_box(
    image: UploadFile = File(...),  # noqa: B008
    x1: int = Form(...),  # noqa: B008
    y1: int = Form(...),  # noqa: B008
    x2: int = Form(...),  # noqa: B008
    y2: int = Form(...),  # noqa: B008
):
    predictor = get_predictor()

    try:
        img_rgb = _read_image(image)
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "detail": str(e)},
        )

    predictor.set_image(img_rgb)
    input_box = np.array([[x1, y1, x2, y2]])

    masks, scores, _ = predictor.predict(
        point_coords=None,
        point_labels=None,
        box=input_box,
        multimask_output=True,
    )

    best_idx = np.argmax(scores)
    best_score = float(scores[best_idx])
    mask_area = int(masks[best_idx].sum())

    return SegmentBoxResponse(
        best_score=best_score,
        box=[x1, y1, x2, y2],
        mask_area_px=mask_area,
    )
