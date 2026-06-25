"""
Point 分割 CLI 脚本
====================

通过单点坐标 Prompt 调用 SAM2 进行交互式分割。
输出 mask 遮罩图 + 可视化叠加图 + 记录 manifest。

数据流：
  输入图片 → SAM2ImagePredictor.set_image() → encode image feature
    ↓
  point (x, y) → predict(point_coords, point_labels) → masks + scores + logits
    ↓
  取 best_score 对应的 mask → 保存 mask PNG + 叠加 overlay
    ↓
  manifest JSONL 追加

使用方式：
  python scripts/02_segment_point.py --image data/images/sample_01.jpg --x 400 --y 300
"""

import argparse
import json
import os

import cv2
import numpy as np
import torch
from sam2.build_sam import build_sam2
from sam2.sam2_image_predictor import SAM2ImagePredictor


def main():
    # ── 1. 解析命令行参数 ────────────────────────────────
    parser = argparse.ArgumentParser(description="SAM 2 Point Segmentation")
    parser.add_argument("--image", required=True, help="输入图片路径")
    parser.add_argument("--x", type=int, required=True, help="目标点 X 坐标")
    parser.add_argument("--y", type=int, required=True, help="目标点 Y 坐标")
    parser.add_argument(
        "--label", type=int, default=1,
        help="1=正样本(目标), 0=负样本(背景)"
    )
    args = parser.parse_args()

    print(f"[segment-point] image={args.image}")
    print(f"[segment-point] point=({args.x},{args.y}), label={args.label}")

    # ── 2. 设备检测 ──────────────────────────────────────
    # Apple Silicon (M1/M2/M3/M4) 使用 mps 后端加速
    device = "mps" if torch.backends.mps.is_available() else "cpu"

    # ── 3. 初始化 SAM2 模型 ──────────────────────────────
    checkpoint = "models/sam2/checkpoints/sam2.1_hiera_tiny.pt"
    # 模型配置文件名相对于 SAM2 源码包内的 configs/ 目录
    model_cfg = "configs/sam2.1/sam2.1_hiera_t.yaml"

    model = build_sam2(model_cfg, checkpoint, device=device)
    predictor = SAM2ImagePredictor(model)

    # ── 4. 图片加载 + 编码 ───────────────────────────────
    image_bgr = cv2.imread(args.image)
    if image_bgr is None:
        print(f"❌ 错误: 无法读取图片 {args.image}")
        return

    # SAM2 的 set_image() 内部完成图像编码器的前向传播，
    # 后续 predict() 直接在编码特征上解码，无需重复推理
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    predictor.set_image(image_rgb)

    # ── 5. Point Prompt 推理 ─────────────────────────────
    # input_point: [N, 2] — N 个点的 (x, y) 坐标
    # input_label: [N] — 每个点的标签 (1=前景, 0=背景)
    # multimask_output=True: 返回多个候选 mask，按 score 取最优
    input_point = np.array([[args.x, args.y]])
    input_label = np.array([args.label])

    masks, scores, logits = predictor.predict(
        point_coords=input_point,
        point_labels=input_label,
        multimask_output=True,
    )

    # ── 6. 取最优 mask ───────────────────────────────────
    best_idx = np.argmax(scores)
    best_mask = masks[best_idx]
    best_score = scores[best_idx]
    print(f"[segment-point] best_score={best_score:.2f}")

    # ── 7. 输出目录 ──────────────────────────────────────
    os.makedirs("outputs/masks", exist_ok=True)
    os.makedirs("outputs/overlays", exist_ok=True)
    os.makedirs("outputs/manifests", exist_ok=True)

    base_name = os.path.splitext(os.path.basename(args.image))[0]
    mask_path = f"outputs/masks/{base_name}_point_mask.png"
    overlay_path = f"outputs/overlays/{base_name}_point_overlay.png"

    # ── 8. 保存 mask ─────────────────────────────────────
    mask_u8 = (best_mask * 255).astype(np.uint8)
    cv2.imwrite(mask_path, mask_u8)
    print(f"[segment-point] mask saved: {mask_path}")

    # ── 9. 渲染 overlay（绿色半透明 + 红色点击标记）───
    overlay = image_bgr.copy()
    color = np.array([0, 255, 0], dtype=np.uint8)  # 绿色 (BGR)

    # 修复：将浮点 mask 转为布尔型
    best_mask_bool = best_mask > 0

    overlay[best_mask_bool] = overlay[best_mask_bool] * 0.5 + color * 0.5
    cv2.circle(overlay, (args.x, args.y), 5, (0, 0, 255), -1)  # 红色标记点
    cv2.imwrite(overlay_path, overlay)
    print(f"[segment-point] overlay saved: {overlay_path}")

    # ── 10. manifest ──────────────────────────────────────
    manifest_path = "outputs/manifests/segmentation_manifest.jsonl"
    with open(manifest_path, "a", encoding="utf-8") as f:
        record = {
            "image": args.image,
            "type": "point",
            "point": [args.x, args.y],
            "score": float(best_score),
            "mask_path": mask_path,
            "overlay_path": overlay_path,
        }
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"[segment-point] manifest appended: {manifest_path}")


if __name__ == "__main__":
    main()