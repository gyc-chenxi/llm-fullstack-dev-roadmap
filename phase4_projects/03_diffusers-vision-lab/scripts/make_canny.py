"""
Canny 边缘检测预处理脚本
========================

将输入图像转换为 Canny 边缘图，作为 ControlNet 的条件输入。

Canny 边缘检测参数：
  - low_threshold (默认 100): 低阈值，低于此的像素被抑制
  - high_threshold (默认 200): 高阈值，高于此的像素被保留为强边缘

数据流：
  输入图像 (RGB) → cv2.Canny() → 边缘图 (灰度)
    → stack 为三通道 → 保存为 PNG

运行：
  python scripts/make_canny.py \
    --input assets/input/sample.png \
    --output assets/control/sample_canny.png \
    --low 100 --high 200
"""

import argparse
from pathlib import Path
import cv2
import numpy as np
from PIL import Image


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--low", type=int, default=100)
    parser.add_argument("--high", type=int, default=200)
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 加载 RGB 图像 → numpy 数组
    img = Image.open(input_path).convert("RGB")
    arr = np.array(img)

    # Canny 边缘检测
    # 输出: 单通道灰度图（0=非边缘, 255=边缘）
    edges = cv2.Canny(arr, args.low, args.high)

    # ControlNet 需要三通道输入，将单通道灰度图堆叠为三通道
    edges_rgb = np.stack([edges, edges, edges], axis=2)

    Image.fromarray(edges_rgb).save(output_path)
    print(f"✅ canny saved: {output_path}")


if __name__ == "__main__":
    main()