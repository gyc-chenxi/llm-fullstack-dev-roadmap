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