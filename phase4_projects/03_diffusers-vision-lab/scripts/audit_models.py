from pathlib import Path

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
            "text_encoder_2",
            "unet",
            "vae",
        ],
    },
    "ControlNet Canny": {
        "path": ROOT / "controlnet-canny",
        "required": [
            "config.json",
        ],
    },
}

WEIGHT_EXTS = {".safetensors", ".bin", ".ckpt", ".pt"}

def dir_size_gb(path: Path) -> float:
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
    if not path.exists():
        return 0
    return sum(1 for p in path.rglob("*") if p.is_file() and p.suffix in WEIGHT_EXTS)

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
