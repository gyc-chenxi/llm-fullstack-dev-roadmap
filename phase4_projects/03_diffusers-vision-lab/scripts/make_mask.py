"""
Inpainting 遮罩生成脚本
========================

根据矩形区域生成二值遮罩图像，作为 Inpaint pipeline 的 mask_image 输入。

遮罩约定（与 Diffusers Inpaint 一致）：
  - 白色 (255) = 需要修复/重绘的区域
  - 黑色 (0) = 保留原始像素的区域

数据流：
  --box x1,y1,x2,y2 → PIL.ImageDraw.rectangle(mask, fill=255)
    → 保存为灰度 PNG

运行：
  python scripts/make_mask.py \
    --input assets/input/sample.png \
    --output assets/masks/sample_mask.png \
    --box 100,100,400,400
"""

import argparse
from pathlib import Path
from PIL import Image, ImageDraw


def parse_box(s: str):
    """解析 "x1,y1,x2,y2" 格式的矩形坐标字符串。"""
    parts = [int(x.strip()) for x in s.split(",")]
    if len(parts) != 4:
        raise ValueError("--box must be x1,y1,x2,y2")
    return tuple(parts)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--box", required=True, help="x1,y1,x2,y2")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 以输入图像尺寸为基础创建全黑遮罩
    img = Image.open(input_path).convert("RGB")
    mask = Image.new("L", img.size, 0)  # 全黑 = 保留区域
    draw = ImageDraw.Draw(mask)
    draw.rectangle(parse_box(args.box), fill=255)  # 白色 = 修复区域

    mask.save(output_path)
    print(f"✅ mask saved: {output_path}")


if __name__ == "__main__":
    main()