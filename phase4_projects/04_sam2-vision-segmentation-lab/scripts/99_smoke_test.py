#!/usr/bin/env python3
"""
冒烟测试脚本
-----------
快速串联验证项目的核心链路是否通畅：
  1. 模型加载 → Point 分割 → Mask 输出
  2. FastAPI 服务健康检查
  3. 项目包导入完整性
"""
from __future__ import annotations

import os
import sys


def test_imports() -> bool:
    """验证项目所有核心模块可成功导入。"""
    modules = [
        ("sam2_lab.device", "device 检测模块"),
        ("sam2_lab.mask.postprocess", "mask 后处理"),
        ("sam2_lab.mask.quality", "mask 质量报告"),
        ("sam2_lab.utils.manifest", "manifest 记录器"),
    ]
    all_ok = True
    for module_name, _desc in modules:
        try:
            __import__(module_name)
            print(f"  ✅ import {module_name}")
        except ImportError as e:
            print(f"  ❌ import {module_name} — {e}")
            all_ok = False
    return all_ok


def test_point_segmentation() -> bool:
    """使用 sample_01.jpg 执行一次真实 Point 分割。"""
    import cv2
    import numpy as np
    import torch
    from sam2.build_sam import build_sam2
    from sam2.sam2_image_predictor import SAM2ImagePredictor

    image_path = "data/images/sample_01.jpg"
    if not os.path.exists(image_path):
        print(f"  ⚠️  跳过 Point 分割测试 — 图片不存在: {image_path}")
        return True  # 不算失败

    checkpoint = "models/sam2/checkpoints/sam2.1_hiera_tiny.pt"
    if not os.path.exists(checkpoint):
        print("  ⚠️  跳过 Point 分割测试 — checkpoint 不存在，先运行 make download-sam2")
        return True

    try:
        device = "mps" if torch.backends.mps.is_available() else "cpu"

        model = build_sam2(
            "configs/sam2.1/sam2.1_hiera_t.yaml", checkpoint, device=device
        )
        predictor = SAM2ImagePredictor(model)

        img = cv2.imread(image_path)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        predictor.set_image(img_rgb)

        point = np.array([[400, 300]])
        label = np.array([1])
        masks, scores, _ = predictor.predict(
            point_coords=point,
            point_labels=label,
            multimask_output=True,
        )

        best_idx = np.argmax(scores)
        best_score = float(scores[best_idx])
        mask_area = int(masks[best_idx].sum())

        print(f"  ✅ Point 分割成功 — best_score={best_score:.3f}, mask_area={mask_area}px")

        # 验证输出目录
        os.makedirs("outputs/masks", exist_ok=True)
        mask_u8 = (masks[best_idx].astype(np.uint8)) * 255
        cv2.imwrite("outputs/masks/smoke_test_mask.png", mask_u8)
        print("  ✅ smoke_test_mask 已保存")

        return True
    except Exception as e:
        print(f"  ❌ Point 分割失败: {e}")
        return False


def test_api_health() -> bool:
    """使用 FastAPI TestClient 测试 API 健康检查。"""
    try:
        from fastapi.testclient import TestClient

        from sam2_lab.api.server import app

        client = TestClient(app)
        response = client.get("/health")
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ API /health 响应 — status={data['status']}, device={data.get('device')}")
            return True
        else:
            print(f"  ❌ API /health 返回 {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ API 健康检查失败: {e}")
        return False


def main():
    print("=" * 55)
    print("  SAM 2 Lab — 冒烟测试")
    print("=" * 55)

    results = {}

    print("\n🧪 1. 核心模块导入")
    results["imports"] = test_imports()

    print("\n🧪 2. Point 分割端到端")
    results["segmentation"] = test_point_segmentation()

    print("\n🧪 3. FastAPI 健康检查")
    results["api"] = test_api_health()

    print("\n" + "=" * 55)
    passed = sum(1 for v in results.values() if v)
    total = len(results)

    if passed == total:
        print(f"  ✅ 冒烟测试全部通过 ({passed}/{total})")
    else:
        print(f"  ❌ 冒烟测试 {passed}/{total} 通过")
        failed = [k for k, v in results.items() if not v]
        print(f"  失败项: {', '.join(failed)}")

    print("=" * 55)

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
