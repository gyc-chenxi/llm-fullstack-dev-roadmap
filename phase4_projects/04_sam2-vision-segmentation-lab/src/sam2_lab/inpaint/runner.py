"""
Inpaint Runner
-------------
编排 SAM2 分割 → Mask 后处理 → Diffusers Inpaint 的完整管线。
可作为 CLI 脚本的后端，也可被 Gradio UI 调用。
"""
from __future__ import annotations

import cv2
import numpy as np
from PIL import Image

from sam2_lab.inpaint.pipeline import InpaintPipeline
from sam2_lab.mask.postprocess import postprocess_mask
from sam2_lab.sam.image_predictor import ImagePredictor
from sam2_lab.sam.loader import load_image_predictor


class InpaintRunner:
    """编排 SAM2 分割 + Diffusers Inpaint 的完整流程。

    用法:
        runner = InpaintRunner()
        runner.load_models()
        result = runner.run(
            image_path="data/images/sample_01.jpg",
            x=400, y=300,  # point prompt
            prompt="a clean background",
        )
    """

    def __init__(self):
        self._predictor: ImagePredictor | None = None
        self._inpaint: InpaintPipeline | None = None
        self._loaded = False

    def load_models(self) -> None:
        """加载 SAM2 和 Inpaint 两个模型。"""
        if self._loaded:
            return

        print("[InpaintRunner] 加载 SAM2 模型...")
        sam2_predictor = load_image_predictor()
        self._predictor = ImagePredictor(sam2_predictor)

        print("[InpaintRunner] 加载 Inpaint 模型...")
        self._inpaint = InpaintPipeline()

        self._loaded = True
        print("[InpaintRunner] 全部模型加载完成 ✓")

    def run_from_point(
        self,
        image: np.ndarray,
        x: int,
        y: int,
        prompt: str = "a clean background, studio lighting",
        **inpaint_kwargs,
    ) -> dict:
        """从 Point Prompt 开始，执行 分割→后处理→修复 全流程。

        Args:
            image: BGR 格式的 numpy 图片数组 (H, W, 3)。
            x, y: 点坐标。
            prompt: Inpaint 生成提示词。
            **inpaint_kwargs: 传递给 InpaintPipeline.run() 的额外参数。

        Returns:
            {
                "mask": np.ndarray (bool),
                "mask_processed": np.ndarray (bool),
                "score": float,
                "inpaint_result": PIL.Image,
            }
        """
        if not self._loaded:
            self.load_models()

        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Step 1: SAM2 Point 分割
        self._predictor.set_image(image_rgb)
        mask, score = self._predictor.predict_from_point(x, y)

        # Step 2: Mask 后处理
        mask_processed = postprocess_mask(mask)

        # Step 3: 准备 Inpaint 输入
        pil_image = Image.fromarray(image_rgb)
        pil_mask = Image.fromarray((mask_processed.astype(np.uint8)) * 255)

        # Step 4: Inpaint
        inpaint_result = self._inpaint.run(pil_image, pil_mask, prompt=prompt, **inpaint_kwargs)

        return {
            "mask": mask,
            "mask_processed": mask_processed,
            "score": score,
            "inpaint_result": inpaint_result,
        }

    def run_from_box(
        self,
        image: np.ndarray,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        prompt: str = "a clean background, studio lighting",
        **inpaint_kwargs,
    ) -> dict:
        """从 Box Prompt 开始的全流程。"""
        if not self._loaded:
            self.load_models()

        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        self._predictor.set_image(image_rgb)
        mask, score = self._predictor.predict_from_box(x1, y1, x2, y2)

        mask_processed = postprocess_mask(mask)

        pil_image = Image.fromarray(image_rgb)
        pil_mask = Image.fromarray((mask_processed.astype(np.uint8)) * 255)

        inpaint_result = self._inpaint.run(pil_image, pil_mask, prompt=prompt, **inpaint_kwargs)

        return {
            "mask": mask,
            "mask_processed": mask_processed,
            "score": score,
            "inpaint_result": inpaint_result,
        }

    def run_from_mask(
        self,
        image: np.ndarray,
        mask: np.ndarray,
        prompt: str = "a clean background, studio lighting",
        **inpaint_kwargs,
    ) -> Image.Image:
        """从已有 mask 直接执行 Inpaint（跳过 SAM2 分割）。

        Args:
            image: BGR 格式 numpy 数组。
            mask: bool 类型 numpy 数组。
            prompt: 生成提示词。

        Returns:
            PIL Image。
        """
        if not self._loaded:
            self.load_models()

        if mask.dtype != bool:
            mask = mask > 127

        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(image_rgb)
        pil_mask = Image.fromarray((mask.astype(np.uint8)) * 255)

        return self._inpaint.run(pil_image, pil_mask, prompt=prompt, **inpaint_kwargs)

    @property
    def is_loaded(self) -> bool:
        return self._loaded
