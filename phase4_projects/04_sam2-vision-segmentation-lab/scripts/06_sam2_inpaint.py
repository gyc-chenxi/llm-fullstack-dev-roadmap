"""
Inpaint 分割+修复 CLI 脚本
==========================

使用 SAM2 分割目标区域 + Diffusers Inpaint 重绘该区域。
一个脚本串联两个模型，实现"点击选定 → 智能替换"的完整管线。

数据流：
  SAM2 Point 分割 → 保存 mask → StableDiffusionInpaintPipeline → 保存结果

使用方式：
  # 需要先下载 diffusers inpainting 模型（自动缓存到 ~/.cache/huggingface）
  python scripts/06_sam2_inpaint.py \
    --image data/images/sample_01.jpg \
    --mask outputs/masks/sample_01_point_mask.png \
    --prompt "a clean futuristic background"
"""

import argparse
import os

import torch
from diffusers import StableDiffusionInpaintPipeline
from PIL import Image


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True, help="原始图片路径")
    parser.add_argument("--mask", required=True, help="SAM2 输出的黑白 mask 路径")
    parser.add_argument("--prompt", required=True, help="Inpaint 生成提示词")
    args = parser.parse_args()

    print("[inpaint] loading StableDiffusionInpaintPipeline")

    # 使用官方模型 ID，Diffusers 会自动寻找本地缓存
    # 本地缓存通常位于 ~/.cache/huggingface/hub/
    model_id = "runwayml/stable-diffusion-inpainting"

    device = "mps" if torch.backends.mps.is_available() else "cpu"

    # Apple Silicon 上使用 float32 确保算子兼容性
    pipe = StableDiffusionInpaintPipeline.from_pretrained(
        model_id,
        torch_dtype=torch.float32,
        safety_checker=None,  # 学习环境关闭安全检查以提升速度
    ).to(device)

    pipe.enable_attention_slicing()
    print(f"[inpaint] device={device} dtype=float32 attention_slicing=True")

    # 调整到 512×512：SD1.5 Inpaint 的最佳工作分辨率
    init_image = Image.open(args.image).convert("RGB").resize((512, 512))
    mask_image = Image.open(args.mask).convert("RGB").resize((512, 512))

    print(f"🎨 开始基于 Prompt 重绘区域: {args.prompt}")
    output = pipe(
        prompt=args.prompt,
        image=init_image,
        mask_image=mask_image,
        num_inference_steps=25,
        guidance_scale=7.5,
    ).images[0]

    os.makedirs("outputs/inpaint", exist_ok=True)
    base_name = os.path.splitext(os.path.basename(args.image))[0]
    out_path = f"outputs/inpaint/{base_name}_inpaint.png"

    output.save(out_path)
    print(f"[inpaint] output saved: {out_path}")


if __name__ == "__main__":
    main()