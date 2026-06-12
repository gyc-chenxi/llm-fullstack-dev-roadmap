"""
Diffusers Inpaint 管线封装
--------------------------
封装 StableDiffusionInpaintPipeline，提供 MPS 友好的图像修复接口。
"""
from __future__ import annotations

import torch
from diffusers import StableDiffusionInpaintPipeline
from PIL import Image

DEFAULT_MODEL_PATH = "models/diffusers/stable-diffusion-inpainting"
DEFAULT_FALLBACK_REPO = "runwayml/stable-diffusion-inpainting"


class InpaintPipeline:
    """Stable Diffusion Inpaint 管线。

    用法:
        pipe = InpaintPipeline()
        result = pipe.run(original_image, mask_image, prompt="a clean background")
    """

    def __init__(
        self,
        model_path: str = DEFAULT_MODEL_PATH,
        fallback_repo: str = DEFAULT_FALLBACK_REPO,
        device: str | None = None,
        torch_dtype: torch.dtype | None = None,
        enable_attention_slicing: bool = True,
    ):
        if device is None:
            if torch.backends.mps.is_available():
                device = "mps"
            elif torch.cuda.is_available():
                device = "cuda"
            else:
                device = "cpu"

        if torch_dtype is None:
            if device == "cuda":
                torch_dtype = torch.float16
            else:
                # MPS/CPU 使用 float32 避免算子兼容问题
                torch_dtype = torch.float32

        self.device = device
        self.torch_dtype = torch_dtype

        # 优先加载本地缓存模型，失败则回退到在线仓库
        try:
            self._pipe = StableDiffusionInpaintPipeline.from_pretrained(
                model_path,
                torch_dtype=torch_dtype,
                local_files_only=True,
                safety_checker=None,
            ).to(device)
            print(f"[InpaintPipeline] 从本地加载模型: {model_path}")
        except Exception:
            print(f"[InpaintPipeline] 本地模型不可用，从 HF 下载: {fallback_repo}")
            self._pipe = StableDiffusionInpaintPipeline.from_pretrained(
                fallback_repo,
                torch_dtype=torch_dtype,
                safety_checker=None,
            ).to(device)

        if enable_attention_slicing:
            self._pipe.enable_attention_slicing()
            print("[InpaintPipeline] attention_slicing 已启用")

        print(f"[InpaintPipeline] 就绪 — device={device}, dtype={torch_dtype}")

    def run(
        self,
        image: Image.Image,
        mask: Image.Image,
        prompt: str = "a clean background, studio lighting",
        negative_prompt: str = "low quality, blurry, watermark, distorted",
        num_inference_steps: int = 25,
        guidance_scale: float = 7.5,
        width: int = 512,
        height: int = 512,
        seed: int = 42,
    ) -> Image.Image:
        """执行图像修复。

        Args:
            image: 原始图片（PIL Image，RGB）。
            mask: 黑白 mask（PIL Image），白色区域会被重绘。
            prompt: 正向提示词。
            negative_prompt: 负向提示词。
            num_inference_steps: 去噪步数。
            guidance_scale: CFG 引导强度。
            width, height: 输出尺寸。
            seed: 随机种子（可复现）。

        Returns:
            修复后的 PIL Image。
        """
        # 调整到目标尺寸
        image_resized = image.resize((width, height))
        mask_resized = mask.resize((width, height))

        generator = torch.Generator(device="cpu").manual_seed(seed)

        output = self._pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            image=image_resized,
            mask_image=mask_resized,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
            generator=generator,
        ).images[0]

        return output
