"""
全自动 Mask 分割 CLI 脚本
==========================

使用 SAM2AutomaticMaskGenerator 对整张图片进行全自动分割，
无需手动指定任何 prompt。输出 top-10 最大 mask 的 PNG 文件
以及 JSON 格式的检测报告。

数据流：
  输入图片 → SAM2AutomaticMaskGenerator.generate(image_rgb)
    → list[dict]（每个 dict 含 segmentation, area, bbox, predicted_iou 等）
    → 按面积排序 → 取 top 10 → 保存 PNG + 报告 JSON

使用方式：
  python scripts/04_segment_auto.py --image data/images/sample_01.jpg
"""

import argparse
import json
import os

import cv2
import numpy as np
import torch
from sam2.automatic_mask_generator import SAM2AutomaticMaskGenerator
from sam2.build_sam import build_sam2


def main():
    parser = argparse.ArgumentParser(description="SAM 2 Auto Segmentation")
    parser.add_argument("--image", required=True, help="输入图片路径")
    args = parser.parse_args()

    # MPS 对底层大量并发矩阵运算支持较好
    device = "mps" if torch.backends.mps.is_available() else "cpu"

    checkpoint = "models/sam2/checkpoints/sam2.1_hiera_tiny.pt"
    model_cfg = "configs/sam2.1/sam2.1_hiera_t.yaml"

    model = build_sam2(model_cfg, checkpoint, device=device)
    mask_generator = SAM2AutomaticMaskGenerator(model)

    image_bgr = cv2.imread(args.image)
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

    print(f"🚀 正在对 {args.image} 进行全图自动分割，这需要一点时间...")
    masks = mask_generator.generate(image_rgb)
    print(f"[segment-auto] detected_masks={len(masks)}")

    os.makedirs("outputs/reports", exist_ok=True)
    os.makedirs("outputs/masks", exist_ok=True)
    base_name = os.path.splitext(os.path.basename(args.image))[0]

    # 按面积降序排列，取前 10 个最大 mask 导出演示
    masks = sorted(masks, key=(lambda x: x["area"]), reverse=True)
    top_masks = masks[:10]

    report_data = {"total_detected": len(masks), "top_10_areas": []}

    for i, mask_data in enumerate(top_masks):
        mask_bool = mask_data["segmentation"]
        mask_u8 = (mask_bool * 255).astype(np.uint8)
        mask_path = f"outputs/masks/{base_name}_auto_{i}.png"
        cv2.imwrite(mask_path, mask_u8)
        report_data["top_10_areas"].append({"index": i, "area": mask_data["area"]})

    print("[segment-auto] top10 masks exported")

    report_path = f"outputs/reports/{base_name}_auto_masks.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)
    print(f"[segment-auto] report saved: {report_path}")


if __name__ == "__main__":
    main()