"""
延迟基准测试脚本
================

测量不同配置下 diffusers pipeline 的端到端生成延迟。
可测试不同模型、推理步数、分辨率组合的性能表现。

数据流：
  脚本 → generate_from_config(cfg)
    → build_pipeline() → pipe(**kwargs).images[0]
    → 记录 latency_sec → 输出汇总统计

运行：
  python scripts/bench_latency.py --config configs/sd15_txt2img.yaml

输出：
  [bench] task=txt2img steps=25 resolution=512x512 latency=3.45s
"""

import argparse
import time

import torch

from diffusers_lab.config import load_yaml
from diffusers_lab.pipelines import build_pipeline


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/sd15_txt2img.yaml")
    parser.add_argument("--warmup", type=int, default=1, help="预热轮数")
    parser.add_argument("--runs", type=int, default=3, help="正式测试轮数")
    args = parser.parse_args()

    cfg = load_yaml(args.config)
    pipe, device, dtype = build_pipeline(cfg)

    # 构建输入参数
    generator = torch.Generator(device="cpu").manual_seed(int(cfg.get("seed", 42)))
    kwargs = {
        "prompt": cfg["prompt"],
        "negative_prompt": cfg.get("negative_prompt", ""),
        "num_inference_steps": int(cfg.get("num_inference_steps", 25)),
        "guidance_scale": float(cfg.get("guidance_scale", 7.5)),
        "width": int(cfg.get("width", 512)),
        "height": int(cfg.get("height", 512)),
        "generator": generator,
    }

    print(f"[bench] warmup={args.warmup} runs={args.runs}")

    # 预热：让模型加载和 CUDA 图编译完成
    for i in range(args.warmup):
        _ = pipe(**kwargs).images[0]
        print(f"  warmup {i+1}/{args.warmup} done")

    # 正式测量
    latencies = []
    for i in range(args.runs):
        t0 = time.time()
        _ = pipe(**kwargs).images[0]
        lat = time.time() - t0
        latencies.append(lat)
        print(f"  run {i+1}/{args.runs}: {lat:.3f}s")

    # 汇总
    avg = sum(latencies) / len(latencies)
    print(f"\n[result] device={device} dtype={dtype}")
    print(f"[result] steps={kwargs['num_inference_steps']} "
          f"resolution={kwargs['width']}x{kwargs['height']}")
    print(f"[result] avg={avg:.3f}s  min={min(latencies):.3f}s  max={max(latencies):.3f}s")


if __name__ == "__main__":
    main()