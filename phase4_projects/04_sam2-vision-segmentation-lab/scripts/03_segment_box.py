import argparse
import json
import os

import cv2
import numpy as np
import torch
from sam2.build_sam import build_sam2
from sam2.sam2_image_predictor import SAM2ImagePredictor

# 尝试导入工程骨架中定义好的质量报告函数
try:
    from sam2_lab.mask.quality import mask_quality_report
except ImportError:
    # 如果没找到，提供一个简单的 fallback 函数，防止代码报错崩溃
    def mask_quality_report(mask):
        return {"area_px": int(mask.sum()), "note": "Basic fallback report"}

def main():
    # 1. 解析 Box (边界框) 的命令行参数
    parser = argparse.ArgumentParser(description="SAM 2 Box Segmentation")
    parser.add_argument("--image", required=True, help="输入图片路径")
    parser.add_argument("--x1", type=int, required=True, help="框左上角 X 坐标")
    parser.add_argument("--y1", type=int, required=True, help="框左上角 Y 坐标")
    parser.add_argument("--x2", type=int, required=True, help="框右下角 X 坐标")
    parser.add_argument("--y2", type=int, required=True, help="框右下角 Y 坐标")
    args = parser.parse_args()

    print(f"[segment-box] box=[{args.x1},{args.y1},{args.x2},{args.y2}]")

    # 2. 自动判定设备 (Mac M 系列使用 mps)
    device = "mps" if torch.backends.mps.is_available() else "cpu"

    # 3. 初始化 SAM 2 模型 (已规避配置文件路径找不到的报错)
    checkpoint = "models/sam2/checkpoints/sam2.1_hiera_tiny.pt"
    model_cfg = "configs/sam2.1/sam2.1_hiera_t.yaml" 
    
    model = build_sam2(model_cfg, checkpoint, device=device)
    predictor = SAM2ImagePredictor(model)

    # 4. 加载图片
    image_bgr = cv2.imread(args.image)
    if image_bgr is None:
        print(f"❌ 错误: 无法读取图片 {args.image}")
        return
    
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    predictor.set_image(image_rgb)

    # 5. 构建 Box Prompt 并预测
    # 格式为: np.array([[x_min, y_min, x_max, y_max]])
    input_box = np.array([[args.x1, args.y1, args.x2, args.y2]])

    masks, scores, logits = predictor.predict(
        point_coords=None,
        point_labels=None,
        box=input_box,
        multimask_output=True,
    )

    # 6. 获取最优 Mask
    best_idx = np.argmax(scores)
    best_mask = masks[best_idx]
    best_score = scores[best_idx]

    # 7. 准备输出目录
    os.makedirs("outputs/masks", exist_ok=True)
    os.makedirs("outputs/overlays", exist_ok=True)
    os.makedirs("outputs/reports", exist_ok=True)
    
    base_name = os.path.splitext(os.path.basename(args.image))[0]
    mask_path = f"outputs/masks/{base_name}_box_mask.png"
    overlay_path = f"outputs/overlays/{base_name}_box_overlay.png"
    report_path = f"outputs/reports/{base_name}_box_quality.json"

    # 8. 保存 Mask
    mask_u8 = (best_mask * 255).astype(np.uint8)
    cv2.imwrite(mask_path, mask_u8)
    print(f"[segment-box] mask saved: {mask_path}")

    # 9. 可视化 Overlay (已规避 NumPy Boolean Index 报错)
    overlay = image_bgr.copy()
    color = np.array([0, 255, 0], dtype=np.uint8)
    best_mask_bool = best_mask > 0 
    
    overlay[best_mask_bool] = overlay[best_mask_bool] * 0.5 + color * 0.5
    # 画出咱们给模型输入的红色提示框 (2是线条粗细)
    cv2.rectangle(overlay, (args.x1, args.y1), (args.x2, args.y2), (0, 0, 255), 2)
    cv2.imwrite(overlay_path, overlay)

    # 10. 生成并保存 Mask 质量报告
    quality_data = mask_quality_report(best_mask_bool)
    quality_data["score"] = float(best_score)
    quality_data["box_prompt"] = [args.x1, args.y1, args.x2, args.y2]

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(quality_data, f, indent=2, ensure_ascii=False)
    print(f"[segment-box] quality report saved: {report_path}")

if __name__ == "__main__":
    main()