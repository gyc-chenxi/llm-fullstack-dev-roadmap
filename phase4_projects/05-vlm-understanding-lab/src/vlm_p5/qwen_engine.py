from __future__ import annotations

from pathlib import Path
from typing import Optional

import torch
from PIL import Image
from qwen_vl_utils import process_vision_info
from transformers import AutoProcessor, Qwen2VLForConditionalGeneration, Qwen2_5_VLForConditionalGeneration

from vlm_p5.device import configure_runtime, get_best_device, get_dtype


class QwenVLEngine:
    def __init__(
        self,
        model_path: str,
        backend: str = "qwen2_5_vl",
        max_new_tokens: int = 512,
        max_pixels: int = 786432,
        min_pixels: int = 3136,
    ) -> None:
        configure_runtime()

        self.model_path = model_path
        self.backend = backend
        self.device = get_best_device()
        self.dtype = get_dtype(self.device)
        self.max_new_tokens = max_new_tokens

        print(f"[QwenVLEngine] device={self.device}, dtype={self.dtype}")
        print(f"[QwenVLEngine] loading model from {model_path}")

        model_cls = (
            Qwen2_5_VLForConditionalGeneration
            if backend == "qwen2_5_vl"
            else Qwen2VLForConditionalGeneration
        )

        self.model = model_cls.from_pretrained(
            model_path,
            torch_dtype=self.dtype,
            low_cpu_mem_usage=True,
        )

        self.model.to(self.device)
        self.model.eval()

        self.processor = AutoProcessor.from_pretrained(
            model_path,
            min_pixels=min_pixels,
            max_pixels=max_pixels,
        )

        print("[QwenVLEngine] model loaded successfully")

    @torch.inference_mode()
    def ask(self, image_path: str, question: str, system_prompt: Optional[str] = None) -> str:
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        # 提前验证图片，避免 PIL 懒加载导致后面报错难定位
        Image.open(path).convert("RGB")

        content = [
            {"type": "image", "image": str(path)},
            {"type": "text", "text": question},
        ]

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": content})

        text = self.processor.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

        image_inputs, video_inputs = process_vision_info(messages)

        inputs = self.processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt",
        )

        inputs = inputs.to(self.device)

        generated_ids = self.model.generate(
            **inputs,
            max_new_tokens=self.max_new_tokens,
            do_sample=False,
        )

        generated_ids_trimmed = [
            out_ids[len(in_ids):]
            for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]

        output = self.processor.batch_decode(
            generated_ids_trimmed,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        )[0]

        return output.strip()