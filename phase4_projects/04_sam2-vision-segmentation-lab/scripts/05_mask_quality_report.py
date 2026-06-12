#!/usr/bin/env python3
"""
Mask 质量报告 CLI 工具
----------------------
读取一张黑白 mask 图片，调用 src/sam2_lab/mask/quality.py 中的
mask_quality_report() 生成 JSON 格式的质量评估报告。

用法示例:
  python scripts/05_mask_quality_report.py \
    --mask outputs/masks/sample_01_point_mask.png \
    --output outputs/reports/sample_01_quality.json
"""
from __future__ import annotations

import argparse
import json
import os

import cv2

from sam2_lab.mask.quality import mask_quality_report


def main():
    parser = argparse.ArgumentParser(
        description="Mask 质量报告生成器 — 分析 mask 的面积/连通域/孔洞/边缘复杂度"
    )
    parser.add_argument(
        "--mask", required=True, help="输入 mask 图片路径（黑白二值图）"
    )
    parser.add_argument(
        "--output",
        default=None,
        help="输出 JSON 报告路径（默认打印到 stdout）",
    )
    parser.add_argument(
        "--min-area",
        type=int,
        default=500,
        help="后处理的最小连通域面积阈值（默认 500px）",
    )
    args = parser.parse_args()

    # ── 1. 读取 mask ───────────────────────────────────────────
    if not os.path.exists(args.mask):
        print(f"❌ 错误: mask 文件不存在: {args.mask}")
        return

    mask_img = cv2.imread(args.mask, cv2.IMREAD_GRAYSCALE)
    if mask_img is None:
        print(f"❌ 错误: 无法读取 mask 图片: {args.mask}")
        return

    # 转为布尔类型
    mask_bool = mask_img > 127
    print(f"[quality-report] 已读取 mask: {args.mask}")
    print(f"[quality-report] 尺寸: {mask_img.shape[1]}x{mask_img.shape[0]}")
    print(f"[quality-report] 前景像素: {mask_bool.sum()}")

    # ── 2. 生成质量报告 ────────────────────────────────────────
    report = mask_quality_report(mask_bool)

    # 附加元信息
    report["source_mask"] = os.path.abspath(args.mask)

    # ── 3. 输出报告 ────────────────────────────────────────────
    json_str = json.dumps(report, indent=2, ensure_ascii=False)

    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(json_str + "\n")
        print(f"[quality-report] 报告已保存: {args.output}")
    else:
        print(json_str)


if __name__ == "__main__":
    main()
