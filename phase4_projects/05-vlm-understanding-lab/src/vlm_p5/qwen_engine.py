"""
Qwen-VL 视觉语言模型引擎
==========================

封装 Qwen2.5-VL / Qwen2-VL 的图像理解和文字生成推理流程，
支持 system_prompt 可选输入，输出纯文本回答。

完整数据流（GPU/MPS 端推理）：

  Image file → PIL.Image.open().convert("RGB")
    │  shape: [H, W, 3], uint8
    │
    └──→ processor.apply_chat_template(messages, add_generation_prompt=True)
         │  将 messages 格式化为模型可识别的文本模板
         │  输出: str (含 <|image_pad|> 等特殊 token)
         │
    └──→ process_vision_info(messages)
         │  从 messages 中提取图片路径并预处理
         │  输出: (image_inputs: list[PIL.Image], video_inputs: list)
         │
    └──→ processor(text=[text], images=image_inputs, return_tensors="pt")
         │  将文本和图片一起编码为模型输入 tensor
         │  输出: { input_ids: [B, L_text], attention_mask: [B, L_text],
         │          pixel_values: [B, C_img, H_img, W_img],
         │          image_grid_thw: [B, 3] }  (Qwen-VL 动态分辨率)
         │
    └──→ model.generate(**inputs, max_new_tokens=512, do_sample=False)
         │  自回归生成，greedy decoding (temperature=0 等效)
         │  输出: generated_ids: [B, L_text + L_gen]
         │
    └──→ 裁剪 prefix: out_ids[len(in_ids):] for each sample
         │  去除输入 token，只保留生成部分
         │
    └──→ processor.batch_decode(trimmed_ids, skip_special_tokens=True)[0]
         │  token IDs → 文本字符串
         │
    └──→ output.strip() → str

关键参数：
  - min_pixels / max_pixels: Qwen-VL 动态分辨率范围，
    图片会缩放到此像素数范围内，超过 max_pixels 会被降采样
  - max_new_tokens: 生成 token 上限，512 对于中英文描述/OCR 通常够用
  - do_sample=False: 贪婪解码，确保输出确定性
  - low_cpu_mem_usage=True: 使用 accelerate 的 low_cpu_mem_usage 模式加载模型，
    避免加载时 CPU 内存峰值

Apple Silicon 注意事项：
  - 显式调用 model.to(device) 而不是 device_map="auto"，
    因为 device_map 在 MPS 上可能触发未知的内存分配错误
  - 整个推理过程用 torch.inference_mode() 包裹，禁用梯度计算以节省内存
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import torch
from PIL import Image
from qwen_vl_utils import process_vision_info
from transformers import AutoProcessor, Qwen2VLForConditionalGeneration, Qwen2_5_VLForConditionalGeneration

from vlm_p5.device import configure_runtime, get_best_device, get_dtype


class QwenVLEngine:
    """Qwen-VL 系列模型推理引擎。

    支持 Qwen2.5-VL 和 Qwen2-VL 两个后端，通过 backend 参数切换。
    """

    def __init__(
        self,
        model_path: str,
        backend: str = "qwen2_5_vl",
        max_new_tokens: int = 512,
        max_pixels: int = 786432,   # ≈ 1024×768
        min_pixels: int = 3136,     # ≈ 56×56
    ) -> None:
        """加载模型和处理器到指定设备。

        Args:
            model_path: 本地模型目录路径
            backend: 模型后端 "qwen2_5_vl" 或 "qwen2_vl"
            max_new_tokens: 最大生成 token 数
            max_pixels: 图片最大像素数（控制 VLM 输入分辨率）
            min_pixels: 图片最小像素数（低于此值会被放大）
        """
        configure_runtime()

        self.model_path = model_path
        self.backend = backend
        self.device = get_best_device()
        self.dtype = get_dtype(self.device)
        self.max_new_tokens = max_new_tokens

        print(f"[QwenVLEngine] device={self.device}, dtype={self.dtype}")
        print(f"[QwenVLEngine] loading model from {model_path}")

        # 根据 backend 选择正确的模型类
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

        # Apple Silicon 上显式 to(device)，不用 device_map="auto"
        self.model.to(self.device)
        self.model.eval()

        # 处理器负责 tokenize + 图片编码，min/max_pixels 控制图片缩放
        self.processor = AutoProcessor.from_pretrained(
            model_path,
            min_pixels=min_pixels,
            max_pixels=max_pixels,
        )

        print("[QwenVLEngine] model loaded successfully")

    @torch.inference_mode()
    def ask(self, image_path: str, question: str, system_prompt: Optional[str] = None) -> str:
        """执行端到端视觉问答推理。

        Args:
            image_path: 本地图片绝对路径
            question: 用户问题（如 "请描述这张图片"）
            system_prompt: 可选的系统级提示词，用于约束回答风格

        Returns:
            模型生成的纯文本回答（已去除首尾空白）

        Raises:
            FileNotFoundError: 图片不存在
        """
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        # 提前用 PIL 打开验证图片，避免后续懒加载导致错误难定位
        Image.open(path).convert("RGB")

        # ---------- 构建 Messages ----------
        # Qwen-VL 的 messages 格式：
        #   [{"role": "user", "content": [
        #       {"type": "image", "image": "path/to/img"},
        #       {"type": "text", "text": "问题文本"}
        #   ]}]
        # 可选 system prompt 放在 user 消息之前
        content = [
            {"type": "image", "image": str(path)},
            {"type": "text", "text": question},
        ]

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": content})

        # ---------- 模板化 → Tokenize ----------
        # apply_chat_template: messages → 模型专用格式文本（含 <image> 占位符等）
        text = self.processor.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

        # process_vision_info: 从 messages 提取图片对象
        image_inputs, video_inputs = process_vision_info(messages)

        # processor: 文本 tokenize + 图片编码 → tensor dict
        inputs = self.processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt",
        )

        # ---------- 送入模型推理 ----------
        inputs = inputs.to(self.device)

        generated_ids = self.model.generate(
            **inputs,
            max_new_tokens=self.max_new_tokens,
            do_sample=False,  # 贪婪解码，输出确定性
        )

        # ---------- 解码输出 ----------
        # 裁剪掉输入 token 前缀，只保留模型生成的新 token
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
