import argparse
import time
from pathlib import Path
import platform
import torch

from .config import load_yaml
from .device import apply_runtime_env
from .manifest import append_manifest, new_run_id
from .pipelines import build_pipeline
from .utils import ensure_dir, load_rgb, load_mask, image_stats

def generate_from_config(cfg: dict) -> dict:
    apply_runtime_env()

    task = cfg["task"]
    seed = int(cfg.get("seed", 42))
    width = int(cfg.get("width", 512))
    height = int(cfg.get("height", 512))
    steps = int(cfg.get("num_inference_steps", cfg.get("steps", 25)))
    guidance_scale = float(cfg.get("guidance_scale", 7.5))

    output_dir = ensure_dir(cfg.get("output_dir", "outputs/images"))
    manifest_path = cfg.get("manifest_path", "outputs/manifests/generation_manifest.jsonl")

    pipe, device, dtype = build_pipeline(cfg)

    generator = torch.Generator(device="cpu").manual_seed(seed)

    kwargs = {
        "prompt": cfg["prompt"],
        "negative_prompt": cfg.get("negative_prompt", ""),
        "num_inference_steps": steps,
        "guidance_scale": guidance_scale,
        "width": width,
        "height": height,
        "generator": generator,
    }

    if task == "img2img":
        kwargs["image"] = load_rgb(cfg["input_image"], size=(width, height))
        kwargs["strength"] = float(cfg.get("strength", 0.55))

    elif task == "inpaint":
        kwargs["image"] = load_rgb(cfg["input_image"], size=(width, height))
        kwargs["mask_image"] = load_mask(cfg["mask_image"], size=(width, height))
        kwargs["strength"] = float(cfg.get("strength", 0.85))

    elif task == "controlnet_canny":
        kwargs["image"] = load_rgb(cfg["control_image"], size=(width, height))
        kwargs["controlnet_conditioning_scale"] = float(
            cfg.get("controlnet_conditioning_scale", 1.0)
        )

    elif task == "sdxl_txt2img":
        # SDXL supports same basic kwargs.
        pass

    run_id = new_run_id(task, seed)
    out_path = output_dir / f"{run_id}.png"

    print(f"[generate] task={task} seed={seed} steps={steps} cfg={guidance_scale} size={width}x{height}")
    t0 = time.time()
    image = pipe(**kwargs).images[0]
    latency = time.time() - t0

    image.save(out_path)
    stats = image_stats(image)

    model_id = cfg.get("model_id") or cfg.get("base_model_id")

    record = {
        "run_id": run_id,
        "task": task,
        "model_id": model_id,
        "prompt": cfg["prompt"],
        "negative_prompt": cfg.get("negative_prompt", ""),
        "seed": seed,
        "num_inference_steps": steps,
        "guidance_scale": guidance_scale,
        "width": width,
        "height": height,
        "dtype": "float32" if dtype == torch.float32 else "float16",
        "device": device,
        "scheduler": pipe.scheduler.__class__.__name__ if hasattr(pipe, "scheduler") else None,
        "lora": cfg.get("lora"),
        "controlnet": {
            "model_id": cfg.get("controlnet_model_id"),
            "control_image": cfg.get("control_image"),
            "conditioning_scale": cfg.get("controlnet_conditioning_scale"),
        } if task == "controlnet_canny" else None,
        "input_image": cfg.get("input_image"),
        "mask_image": cfg.get("mask_image"),
        "latency_sec": round(latency, 3),
        "output_path": str(out_path),
        "image_stats": stats,
        "python": platform.python_version(),
        "torch": torch.__version__,
    }

    append_manifest(manifest_path, record)

    print(f"[output] {out_path}")
    print(f"[manifest] appended {manifest_path}")
    print(f"[stats] {stats}")
    print("✅ done")

    return record

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    cfg = load_yaml(args.config)
    print(f"[config] loaded {args.config}")
    generate_from_config(cfg)

if __name__ == "__main__":
    main()
