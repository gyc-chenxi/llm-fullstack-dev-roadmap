import argparse
import json
import os

import cv2
import numpy as np
import torch
from sam2.build_sam import build_sam2
from sam2.sam2_image_predictor import SAM2ImagePredictor


def main():
    # 1. 解析命令行参数
    parser = argparse.ArgumentParser(description="SAM 2 Point Segmentation")
    parser.add_argument("--image", required=True, help="输入图片路径")
    parser.add_argument("--x", type=int, required=True, help="目标点 X 坐标")
    parser.add_argument("--y", type=int, required=True, help="目标点 Y 坐标")
    parser.add_argument("--label", type=int, default=1, help="1代表正样本(目标), 0代表负样本(背景)")
    args = parser.parse_args()

    print(f"[segment-point] image={args.image}")
    print(f"[segment-point] point=({args.x},{args.y}), label={args.label}")

    # 2. 自动判定设备 (Mac M 系列使用 mps)
    device = "mps" if torch.backends.mps.is_available() else "cpu"

    # 3. 初始化 SAM 2 模型
    checkpoint = "models/sam2/checkpoints/sam2.1_hiera_tiny.pt"
    model_cfg = "configs/sam2.1/sam2.1_hiera_t.yaml" # SAM 2 包内置的配置文件名
    
    model = build_sam2(model_cfg, checkpoint, device=device)
    predictor = SAM2ImagePredictor(model)

    # 4. 加载并预处理图片
    image_bgr = cv2.imread(args.image)
    if image_bgr is None:
        print(f"❌ 错误: 无法读取图片 {args.image}，请检查路径是否正确。")
        return
    
    # SAM 2 期望的输入是 RGB 格式
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    predictor.set_image(image_rgb)

    # 5. 构建 Point Prompt 并进行预测
    input_point = np.array([[args.x, args.y]])
    input_label = np.array([args.label])

    # 预测返回多个层级的 mask，这里开启 multimask_output
    masks, scores, logits = predictor.predict(
        point_coords=input_point,
        point_labels=input_label,
        multimask_output=True,
    )

    # 6. 获取得分最高的最优 Mask
    best_idx = np.argmax(scores)
    best_mask = masks[best_idx]
    best_score = scores[best_idx]
    print(f"[segment-point] best_score={best_score:.2f}")

    # 7. 准备输出目录
    os.makedirs("outputs/masks", exist_ok=True)
    os.makedirs("outputs/overlays", exist_ok=True)
    os.makedirs("outputs/manifests", exist_ok=True)
    
    base_name = os.path.splitext(os.path.basename(args.image))[0]
    mask_path = f"outputs/masks/{base_name}_point_mask.png"
    overlay_path = f"outputs/overlays/{base_name}_point_overlay.png"

    # 8. 保存纯黑白的 Mask 遮罩图
    mask_u8 = (best_mask * 255).astype(np.uint8)
    cv2.imwrite(mask_path, mask_u8)
    print(f"[segment-point] mask saved: {mask_path}")

    # 9. 渲染可视化 Overlay (在原图上叠加绿色半透明 Mask 和红色目标点)
    overlay = image_bgr.copy()
    color = np.array([0, 255, 0], dtype=np.uint8)  # BGR格式的绿色
    
    # 修复：将浮点型的 mask 转换为布尔型 (大于 0 的即为 True)
    best_mask_bool = best_mask > 0 
    
    # 将 Mask 区域与原图按 0.5 的透明度进行混合
    overlay[best_mask_bool] = overlay[best_mask_bool] * 0.5 + color * 0.5
    # 在点击位置画一个红色的点标记
    cv2.circle(overlay, (args.x, args.y), 5, (0, 0, 255), -1)
    cv2.imwrite(overlay_path, overlay)
    print(f"[segment-point] overlay saved: {overlay_path}")

    # 10. 记录 Manifest 数据
    manifest_path = "outputs/manifests/segmentation_manifest.jsonl"
    with open(manifest_path, "a", encoding="utf-8") as f:
        record = {
            "image": args.image,
            "type": "point",
            "point": [args.x, args.y],
            "score": float(best_score),
            "mask_path": mask_path,
            "overlay_path": overlay_path
        }
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"[segment-point] manifest appended: {manifest_path}")

if __name__ == "__main__":
    main()