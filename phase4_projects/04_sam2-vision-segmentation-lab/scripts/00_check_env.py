#!/usr/bin/env python3
"""
环境自检脚本
-----------
检查项目运行所需的全部依赖是否就绪：
  - Python 版本 (>=3.11)
  - PyTorch + MPS/CUDA 可用性
  - OpenCV (cv2)
  - SAM 2 (sam2.build_sam)
  - Diffusers (StableDiffusionInpaintPipeline)
  - FastAPI / Uvicorn
  - Gradio
  - 项目自身包 (sam2_lab)
  - SAM 2 checkpoint 文件是否存在
"""
from __future__ import annotations

import os
import sys


def check_python() -> bool:
    version = sys.version_info
    major, minor = version.major, version.minor
    if major >= 3 and minor >= 11:
        print(f"  ✅ Python {major}.{minor}.{version.micro}")
        return True
    else:
        print(f"  ❌ Python {major}.{minor} — 需要 >= 3.11")
        return False


def check_package(import_name: str, display_name: str | None = None) -> bool:
    """尝试导入一个包，返回是否成功。"""
    label = display_name or import_name
    try:
        __import__(import_name)
        print(f"  ✅ {label}")
        return True
    except ImportError as e:
        print(f"  ❌ {label} — ImportError: {e}")
        return False


def check_torch_mps() -> bool:
    """检查 PyTorch 和 MPS 可用性。"""
    try:
        import torch

        version = torch.__version__
        mps_ok = torch.backends.mps.is_available()
        cuda_ok = torch.cuda.is_available()
        if mps_ok:
            print(f"  ✅ PyTorch {version} (MPS 可用)")
        elif cuda_ok:
            print(f"  ✅ PyTorch {version} (CUDA 可用)")
        else:
            print(f"  ⚠️  PyTorch {version} (仅 CPU — 推理会很慢)")
        return True
    except ImportError as e:
        print(f"  ❌ PyTorch — ImportError: {e}")
        return False


def check_sam2_import() -> bool:
    """检查 sam2 包是否能导入并构建模型。"""
    try:
        from sam2.build_sam import build_sam2  # noqa: F401

        # 不实际加载模型，只检查接口可用
        print("  ✅ sam2 (build_sam2 可用)")
        return True
    except ImportError as e:
        print(f"  ❌ sam2 — ImportError: {e}")
        return False


def check_checkpoint_exists() -> bool:
    """检查 SAM 2 checkpoint 文件是否已下载。"""
    ckpt_path = "models/sam2/checkpoints/sam2.1_hiera_tiny.pt"
    if os.path.exists(ckpt_path):
        size_mb = os.path.getsize(ckpt_path) / (1024 * 1024)
        print(f"  ✅ SAM2 checkpoint ({size_mb:.1f} MB)")
        return True
    else:
        print("  ⚠️  SAM2 checkpoint 未找到 — 运行 make download-sam2 下载")
        return False


def check_sam2_lab() -> bool:
    """检查项目自身包是否可导入。"""
    try:
        from sam2_lab.device import get_device, get_torch_dtype  # noqa: F401
        from sam2_lab.mask.postprocess import postprocess_mask  # noqa: F401
        from sam2_lab.mask.quality import mask_quality_report  # noqa: F401
        from sam2_lab.utils.manifest import append_manifest  # noqa: F401

        device = get_device()
        print(f"  ✅ sam2_lab (device={device})")
        return True
    except ImportError as e:
        print(f"  ❌ sam2_lab — ImportError: {e}")
        return False


def main():
    print("=" * 55)
    print("  SAM 2 Vision Segmentation Lab — 环境自检")
    print("=" * 55)

    results = {}

    print("\n🔍 1. Python 版本")
    results["python"] = check_python()

    print("\n🔍 2. PyTorch + 加速后端")
    results["torch"] = check_torch_mps()

    print("\n🔍 3. 核心依赖包")
    results["cv2"] = check_package("cv2", "opencv-python (cv2)")
    results["numpy"] = check_package("numpy")
    results["PIL"] = check_package("PIL", "Pillow (PIL)")
    results["yaml"] = check_package("yaml", "PyYAML")

    print("\n🔍 4. SAM 2 生态")
    results["sam2"] = check_sam2_import()
    results["checkpoint"] = check_checkpoint_exists()

    print("\n🔍 5. Diffusers 生态")
    results["diffusers"] = check_package("diffusers", "diffusers")
    results["transformers"] = check_package("transformers")

    print("\n🔍 6. API / UI 生态")
    results["fastapi"] = check_package("fastapi")
    results["uvicorn"] = check_package("uvicorn")
    results["gradio"] = check_package("gradio")

    print("\n🔍 7. 项目自身包 (sam2_lab)")
    results["sam2_lab"] = check_sam2_lab()

    # ── 汇总 ───────────────────────────────────────────────────
    print("\n" + "=" * 55)
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    warnings = sum(
        1 for k, v in results.items() if not v and k in ("checkpoint",)
    )

    if passed == total:
        print(f"  ✅ 全部 {total} 项检查通过！环境就绪。")
    elif passed + warnings >= total:
        print(f"  ⚠️  {passed}/{total} 项通过（有 {total - passed} 项需要关注）")
    else:
        print(f"  ❌ {passed}/{total} 项通过（{total - passed} 项失败）")

    print("=" * 55)

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
