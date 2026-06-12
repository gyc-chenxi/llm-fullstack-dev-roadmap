"""
SAM 2 模型加载器
---------------
统一管理 SAM 2 图像预测器、视频预测器和自动 mask 生成器的加载逻辑。
所有加载函数返回可直接使用的模型实例，调用方无需关心底层 build_sam2 细节。
"""
from __future__ import annotations

import torch
from sam2.automatic_mask_generator import SAM2AutomaticMaskGenerator
from sam2.build_sam import build_sam2, build_sam2_video_predictor
from sam2.sam2_image_predictor import SAM2ImagePredictor

DEFAULT_CHECKPOINT = "models/sam2/checkpoints/sam2.1_hiera_tiny.pt"
DEFAULT_MODEL_CFG = "configs/sam2.1/sam2.1_hiera_t.yaml"


def get_device() -> str:
    """自动检测最佳推理设备。"""
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def load_sam2_model(
    checkpoint: str = DEFAULT_CHECKPOINT,
    model_cfg: str = DEFAULT_MODEL_CFG,
    device: str | None = None,
):
    """加载 SAM 2 基础模型（不含预测器包装）。

    Args:
        checkpoint: 模型权重文件路径。
        model_cfg: Hydra 配置文件名（相对于 SAM 2 内部的 configs 目录）。
        device: 推理设备，默认自动检测。

    Returns:
        SAM 2 模型实例（eval 模式）。
    """
    if device is None:
        device = get_device()

    model = build_sam2(model_cfg, checkpoint, device=device)
    print(f"[loader] SAM2 model loaded on {device}")
    return model


def load_image_predictor(
    checkpoint: str = DEFAULT_CHECKPOINT,
    model_cfg: str = DEFAULT_MODEL_CFG,
    device: str | None = None,
) -> SAM2ImagePredictor:
    """加载 SAM 2 图像预测器（用于 Point/Box 交互式分割）。

    Returns:
        SAM2ImagePredictor 实例，可直接调用 set_image() + predict()。
    """
    model = load_sam2_model(checkpoint, model_cfg, device)
    predictor = SAM2ImagePredictor(model)
    print("[loader] SAM2ImagePredictor ready")
    return predictor


def load_auto_mask_generator(
    checkpoint: str = DEFAULT_CHECKPOINT,
    model_cfg: str = DEFAULT_MODEL_CFG,
    device: str | None = None,
    points_per_side: int = 32,
    pred_iou_thresh: float = 0.88,
    stability_score_thresh: float = 0.92,
    min_mask_region_area: int = 500,
) -> SAM2AutomaticMaskGenerator:
    """加载 SAM 2 全自动 Mask 生成器。

    Args:
        points_per_side: 每边的采样点数（越高越精细，但越慢）。
        pred_iou_thresh: 预测 IoU 阈值，低于此值的 mask 被过滤。
        stability_score_thresh: 稳定性分数阈值。
        min_mask_region_area: 最小 mask 区域面积（像素）。

    Returns:
        SAM2AutomaticMaskGenerator 实例。
    """
    model = load_sam2_model(checkpoint, model_cfg, device)
    mask_generator = SAM2AutomaticMaskGenerator(
        model=model,
        points_per_side=points_per_side,
        pred_iou_thresh=pred_iou_thresh,
        stability_score_thresh=stability_score_thresh,
        min_mask_region_area=min_mask_region_area,
    )
    print("[loader] SAM2AutomaticMaskGenerator ready")
    return mask_generator


def load_video_predictor(
    checkpoint: str = DEFAULT_CHECKPOINT,
    model_cfg: str = DEFAULT_MODEL_CFG,
    device: str | None = None,
):
    """加载 SAM 2 视频预测器（用于视频目标追踪）。

    Returns:
        SAM2VideoPredictor 实例。
    """
    if device is None:
        device = get_device()

    predictor = build_sam2_video_predictor(
        config_file=model_cfg,
        ckpt_path=checkpoint,
        device=device,
    )
    print(f"[loader] SAM2VideoPredictor ready on {device}")
    return predictor
