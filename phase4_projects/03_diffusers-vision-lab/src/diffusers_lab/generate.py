"""
图像生成主引擎
==============

核心入口函数 generate_from_config() 串联完整的生成流水线：
  1. 加载配置 → 构建 pipeline → 构建随机生成器
  2. 组装不同任务特有的推理参数（img2img 的 strength、inpainting 的 mask 等）
  3. 调用 pipe(**kwargs) 执行推理 → 保存图像
  4. 记录生成 manifest（JSONL）→ 返回元数据记录

数据流全景：
  cli/api → generate_from_config(cfg)
    ↓
  ┌─ 构建阶段 ──────────────────────────────────────────┐
  │  apply_runtime_env()          ← 设置 MPS fallback   │
  │  build_pipeline(cfg)         ← 加载模型权重到设备  │
  │  torch.Generator(seed)       ← 确定性随机数生成器  │
  └─────────────────────────────────────────────────────┘
    ↓
  ┌─ 参数组装阶段 ──────────────────────────────────────┐
  │  task=img2img:    image + strength                  │
  │  task=inpaint:    image + mask + strength           │
  │  task=controlnet: control_image + cond_scale        │
  │  其他:            prompt + negative_prompt + ...    │
  └─────────────────────────────────────────────────────┘
    ↓
  ┌─ 推理阶段 ──────────────────────────────────────────┐
  │  pipe(**kwargs).images[0]                           │
  │    ↓ 输出: PIL.Image (512×512 或 1024×1024 RGB)     │
  │  image.save(out_path)                                │
  │  image_stats(image) ← 基础统计（min/max/mean）       │
  └─────────────────────────────────────────────────────┘
    ↓
  ┌─ 记录阶段 ──────────────────────────────────────────┐
  │  append_manifest(manifest_path, record)              │
  │  写入 JSONL: {run_id, task, seed, latency, ...}     │
  └─────────────────────────────────────────────────────┘
"""

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
    """
    根据配置字典执行完整的图像生成流程。

    参数：
      cfg: 配置字典（来自 YAML 或 API），必含字段：
        - task: str — 任务类型（txt2img/img2img/inpaint/...）
        - model_id 或 base_model_id: str — 模型路径
        - prompt: str — 正向提示词
        可选：negative_prompt, seed, steps, guidance_scale,
              width, height, input_image, mask_image 等

    返回：
      record: dict — 完整的生成记录（含延迟、输出路径、统计），
              同时追加写入 manifest JSONL 文件

    异常：
      FileNotFoundError: 模型权重或输入图像不存在
      ValueError: 不支持的任务类型
    """
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

    # 在 CPU 上创建生成器，保证 seed 跨设备可复现
    # 后续 .to(device) 由 pipeline 内部处理
    generator = torch.Generator(device="cpu").manual_seed(seed)

    kwargs = {
        "prompt": cfg["prompt"],
        "negative_prompt": cfg.get("negative_prompt", ""),
        "num_inference_steps": steps,        # 去噪步数：越多越精细，但耗时线性增长
        "guidance_scale": guidance_scale,    # CFG 引导强度：7.5 是 SD1.5 的经典平衡点
        "width": width,                       # 生成图像宽度（像素）
        "height": height,                     # 生成图像高度（像素）
        "generator": generator,
    }

    # ── 任务特有参数 ──
    if task == "img2img":
        # 图生图：以输入图像为起点做去噪
        # strength=0.55 → 保留约 55% 的原始图像特征
        kwargs["image"] = load_rgb(cfg["input_image"], size=(width, height))
        kwargs["strength"] = float(cfg.get("strength", 0.55))

    elif task == "inpaint":
        # 图像修复：仅重绘 mask 白色区域
        # strength=0.85 → 重绘区域几乎完全重新生成
        kwargs["image"] = load_rgb(cfg["input_image"], size=(width, height))
        kwargs["mask_image"] = load_mask(cfg["mask_image"], size=(width, height))
        kwargs["strength"] = float(cfg.get("strength", 0.85))

    elif task == "controlnet_canny":
        # ControlNet 控制生成：输入 Canny 边缘图
        # controlnet_conditioning_scale=1.0 表示完全遵循边缘约束
        kwargs["image"] = load_rgb(cfg["control_image"], size=(width, height))
        kwargs["controlnet_conditioning_scale"] = float(
            cfg.get("controlnet_conditioning_scale", 1.0)
        )

    elif task == "sdxl_txt2img":
        # SDXL 文生图：使用相同的通用参数
        # SDXL 原生支持双文本编码器，from_pretrained 自动处理
        pass

    # ── 推理执行 ──
    run_id = new_run_id(task, seed)
    out_path = output_dir / f"{run_id}.png"

    print(f"[generate] task={task} seed={seed} steps={steps} cfg={guidance_scale} size={width}x{height}")
    t0 = time.time()
    image = pipe(**kwargs).images[0]   # 输出: PIL.Image (RGB, [width×height])
    latency = time.time() - t0

    image.save(out_path)
    stats = image_stats(image)          # 输出图像统计信息

    # ── 记录元数据（写入 JSONL manifest） ──
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
    """
    CLI 入口：python -m src.diffusers_lab.generate --config configs/sd15_txt2img.yaml
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    cfg = load_yaml(args.config)
    print(f"[config] loaded {args.config}")
    generate_from_config(cfg)


if __name__ == "__main__":
    main()