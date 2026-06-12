import argparse
import os

import torch
from diffusers import StableDiffusionInpaintPipeline
from PIL import Image


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True, help="原始图片路径")
    parser.add_argument("--mask", required=True, help="SAM 2 抠出的黑白 Mask 路径")
    parser.add_argument("--prompt", required=True, help="生成提示词")
    args = parser.parse_args()

    print("[inpaint] loading StableDiffusionInpaintPipeline")
    # 直接使用官方模型 ID，Diffusers 会自动去你之前下好 11GB 的本地缓存里拿
    model_id = "runwayml/stable-diffusion-inpainting"
    
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    
    # 针对 Mac 架构的防御性配置
    pipe = StableDiffusionInpaintPipeline.from_pretrained(
        model_id, 
        torch_dtype=torch.float32, 
        safety_checker=None # 纯本地学习环境可以关闭安全检查器提升速度
    ).to(device)
    
    pipe.enable_attention_slicing()
    print(f"[inpaint] device={device} dtype=float32 attention_slicing=True")

    # PIL 读取原图和遮罩，需调整为 512x512 以匹配基础 SD 模型的最佳分辨率
    init_image = Image.open(args.image).convert("RGB").resize((512, 512))
    mask_image = Image.open(args.mask).convert("RGB").resize((512, 512))

    print(f"🎨 开始基于 Prompt 重绘区域: {args.prompt}")
    # 执行 Inpaint 生成
    output = pipe(
        prompt=args.prompt,
        image=init_image,
        mask_image=mask_image,
        num_inference_steps=25,
        guidance_scale=7.5
    ).images[0]

    os.makedirs("outputs/inpaint", exist_ok=True)
    base_name = os.path.splitext(os.path.basename(args.image))[0]
    out_path = f"outputs/inpaint/{base_name}_inpaint.png"
    
    output.save(out_path)
    print(f"[inpaint] output saved: {out_path}")

if __name__ == "__main__":
    main()