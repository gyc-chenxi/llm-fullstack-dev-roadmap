"""
SAM 2 图像预测器封装
-------------------
将 SAM2ImagePredictor 的原始 API 封装为更加语义化的高级接口，
调用方无需直接操作 numpy 数组拼接和 multimask_output 细节。
"""
from __future__ import annotations

import numpy as np
from sam2.sam2_image_predictor import SAM2ImagePredictor


class ImagePredictor:
    """SAM 2 图像分割的高级封装。

    用法:
        predictor = ImagePredictor(sam2_predictor)
        predictor.set_image(image_rgb)
        mask, score = predictor.predict_from_point(x=400, y=300)
    """

    def __init__(self, sam2_predictor: SAM2ImagePredictor):
        self._predictor = sam2_predictor
        self._image_set = False

    def set_image(self, image: np.ndarray) -> None:
        """设置待分割的图像（RGB 格式）。

        Args:
            image: RGB 格式的 numpy 数组 (H, W, 3)。
        """
        self._predictor.set_image(image)
        self._image_set = True
        self._image_shape = image.shape[:2]

    def predict_from_point(
        self,
        x: int,
        y: int,
        label: int = 1,
        multimask_output: bool = True,
    ) -> tuple[np.ndarray, float]:
        """基于单点 Prompt 进行分割。

        Args:
            x, y: 点击坐标。
            label: 1=前景, 0=背景。
            multimask_output: 是否输出多个候选 mask。

        Returns:
            (best_mask, best_score) — 得分最高的 mask 及其分数。
        """
        if not self._image_set:
            raise RuntimeError("请先调用 set_image() 设置图片")

        input_point = np.array([[x, y]])
        input_label = np.array([label])

        masks, scores, _ = self._predictor.predict(
            point_coords=input_point,
            point_labels=input_label,
            multimask_output=multimask_output,
        )

        best_idx = np.argmax(scores)
        return masks[best_idx], float(scores[best_idx])

    def predict_from_box(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        multimask_output: bool = True,
    ) -> tuple[np.ndarray, float]:
        """基于矩形框 Prompt 进行分割。

        Args:
            x1, y1: 框左上角坐标。
            x2, y2: 框右下角坐标。
            multimask_output: 是否输出多个候选 mask。

        Returns:
            (best_mask, best_score)
        """
        if not self._image_set:
            raise RuntimeError("请先调用 set_image() 设置图片")

        input_box = np.array([[x1, y1, x2, y2]])

        masks, scores, _ = self._predictor.predict(
            point_coords=None,
            point_labels=None,
            box=input_box,
            multimask_output=multimask_output,
        )

        best_idx = np.argmax(scores)
        return masks[best_idx], float(scores[best_idx])

    def predict_from_points(
        self,
        points: list[tuple[int, int, int]],
        multimask_output: bool = True,
    ) -> tuple[np.ndarray, float]:
        """基于多点 Prompt 进行分割。

        Args:
            points: [(x, y, label), ...] 列表，label 1=前景 0=背景。
            multimask_output: 是否输出多个候选 mask。

        Returns:
            (best_mask, best_score)
        """
        if not self._image_set:
            raise RuntimeError("请先调用 set_image() 设置图片")

        coords = np.array([[p[0], p[1]] for p in points])
        labels = np.array([p[2] for p in points])

        masks, scores, _ = self._predictor.predict(
            point_coords=coords,
            point_labels=labels,
            multimask_output=multimask_output,
        )

        best_idx = np.argmax(scores)
        return masks[best_idx], float(scores[best_idx])
