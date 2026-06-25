"""
本地模型审计脚本
================

扫描 models/ 目录下的所有模型文件夹，检查：
  1. 目录结构完整性（是否包含 model_index.json、subfolders）
  2. 权重文件是否存在（.safetensors / .bin / .ckpt / .pt）
  3. 总磁盘占用

在首次运行或下载新模型后执行，确保模型权重就绪。

运行： python scripts/audit_models.py
"""

from pathlib import Path

# 模型检查清单
# 每个条目定义了期望的模型路径和必需的子目录/文件
ROOT = Path("models")

MODEL_CHECKS = {
    "SD1.5 txt2img": {
        "path": ROOT / "sd15",
        "required": [
            "model_index.json",
            "scheduler",
            "tokenizer",
            "text_encoder",
            "unet",
            "vae",
        ],
    },
    "SD1.5 inpaint": {
        "path": ROOT / "sd15-inpaint",
        "required": [
            "model_index.json",
            "scheduler",
            "tokenizer",
            "text_encoder",
            "unet",
            "vae",
        ],
    },
    "SDXL base": {
        "path": ROOT / "sdxl-base",
        "required": [
            "model_index.json",
            "scheduler",
            "tokenizer",
            "tokenizer_2",
            "text_encoder",
            "text_encoder_2",  # SDXL 的双编码器
            "unet",
            "vae",
        ],
    },
    "ControlNet Canny": {
        "path": ROOT / "controlnet-canny",
        "required": [
            "config.json",  # ControlNet 只有 config.json，没有 model_index.json
        ],
    },
}

# 支持的权重文件扩展名
# .safetensors (推荐): 安全、快速、无 pickle 漏洞
# .bin / .ckpt / .pt: 传统 PyTorch 权重格式
WEIGHT_EXTS = {".safetensors", ".bin", ".ckpt", ".pt"}


def dir_size_gb(path: Path) -> float:
    """递归计算目录总大小（GB）。"""
    total = 0
    if not path.exists():
        return 0.0
    for p in path.rglob("*"):
        if p.is_file():
            try:
                total += p.stat().st_size
            except OSError:
                pass
    return total / 1024 / 1024 / 1024


def count_weight_files(path: Path) -> int:
    """统计目录中权重文件的数量。"""
    if not path.exists():
        return 0
    return sum(1 for p in path.rglob("*") if p.is_file() and p.suffix in WEIGHT_EXTS)


def main():
    print("=" * 72)
    print("Diffusers Vision Lab - Local Model Audit")
    print("=" * 72)

    all_ok = True

    for name, spec in MODEL_CHECKS.items():
        path = spec["path"]
        print(f"\n[{name}]")
        print(f"Path: {path}")

        if not path.exists():
            print("Status: ❌ MISSING DIRECTORY")
            all_ok = False
            continue

        size_gb = dir_size_gb(path)
        weight_count = count_weight_files(path)
        print(f"Size: {size_gb:.2f} GB")
        print(f"Weight files: {weight_count}")

        # 检查必需的子目录/文件是否存在
        missing = [item for item in spec["required"] if not (path / item).exists()]

        if missing:
            print("Required files/dirs: ❌ MISSING")
            for m in missing:
                print(f"  - {m}")
            all_ok = False
        else:
            print("Required files/dirs: ✅ OK")

        if weight_count <= 0:
            print("Weights: ❌ NO WEIGHT FILE FOUND")
            all_ok = False
        else:
            print("Weights: ✅ FOUND")

    print("\n" + "=" * 72)
    if all_ok:
        print("FINAL: ✅ All required model directories look complete.")
    else:
        print("FINAL: ❌ Some models are missing or incomplete.")
    print("=" * 72)


if __name__ == "__main__":
    main()