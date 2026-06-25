"""
LLaVA-OneVision 冒烟测试
==========================

验证 LLaVA 架构的端到端推理管线：
  Image → Vision Encoder (SigLIP/CLIP) → Projector (MLP) → LLM (Qwen2) → Text

与 Qwen-VL 的关键区别：
  - LLaVA 使用独立的 Vision Encoder + Projector 架构，视觉 token 通过 MLP 投影到 LLM 空间
  - Qwen-VL 将视觉编码直接内建在 transformer 中，不需要额外的 projector 层
  - LLaVA 的 processor 不支持 min_pixels/max_pixels（图片统一缩放到模型固定输入尺寸）
  - LLaVA 的 chat_template 使用 {"type": "image"} 不含路径

数据流：
  scene_demo.jpg → Image.open().convert("RGB") → [H,W,3] uint8
    ↓
  conversation template with {"type": "image"} + text question
    ↓
  processor.apply_chat_template(conversation, add_generation_prompt=True)
    → 模型格式文本（含 <image> token）
    ↓
  processor(images=image, text=prompt, return_tensors="pt")
    → inputs: { input_ids: [B, L], attention_mask: [B, L],
                pixel_values: [B, C, H, W] }
    ↓
  model.generate(**inputs, max_new_tokens=256, do_sample=False)
    → generated_ids: [B, L + L_gen]
    ↓
  processor.decode(output[0], skip_special_tokens=True) → 描述文本
"""

from __future__ import annotations

import torch
from PIL import Image
from transformers import LlavaOnevisionForConditionalGeneration, AutoProcessor

from vlm_p5.device import configure_runtime, get_best_device, get_dtype

configure_runtime()

model_path = "models/llava-onevision-qwen2-0.5b-si-hf"
image_path = "assets/samples/scene_demo.jpg"

device = get_best_device()
dtype = get_dtype(device)

print(f"[LLaVA] device={device}, dtype={dtype}")

model = LlavaOnevisionForConditionalGeneration.from_pretrained(
    model_path,
    torch_dtype=dtype,
    low_cpu_mem_usage=True,
)
model.to(device)
model.eval()

processor = AutoProcessor.from_pretrained(model_path)

# LLaVA conversation 格式：content 中使用 {"type": "image"} 占位
conversation = [
    {
        "role": "user",
        "content": [
            {"type": "image"},
            {"type": "text", "text": "Describe this image in detail."},
        ],
    }
]

prompt = processor.apply_chat_template(
    conversation,
    add_generation_prompt=True,
)

image = Image.open(image_path).convert("RGB")

inputs = processor(
    images=image,
    text=prompt,
    return_tensors="pt",
).to(device)

with torch.inference_mode():
    output = model.generate(
        **inputs,
        max_new_tokens=256,
        do_sample=False,
    )

print(processor.decode(output[0], skip_special_tokens=True))
