

# Week04_runbook.md — SAM 2 视觉分割工程实战

> 项目代号：`04_sam2-vision-segmentation-lab`
>  周期：Day 54–56，3 天
>  环境：macOS Apple Silicon M5 / 32GB 统一内存 / Conda `cxllm` / Python 3.11
>  核心目标：从 Diffusers 的“生成图像”进阶到 SAM 2 的“像素级 Mask 工程”，完成 Point / Box / Auto Segmentation、Mask 后处理、质量评估、SAM 2 + Diffusers Inpaint 联动、视频分割追踪。
>  前置项目：P3 已完成 Diffusers 的 txt2img、img2img、inpaint、LoRA、ControlNet、Manifest 记录等生成链路，本项目会直接复用其中的 Diffusers Inpaint 工程经验。

------

## 0. 工程定位

P3 Diffusers 项目的主线是：

```
Prompt → Text Encoder → UNet Denoising → VAE Decode → Image
```

P4 SAM 2 项目的主线变成：

```
Image / Video
  ↓
Prompt: Point / Box / Mask
  ↓
SAM 2 Predictor
  ↓
Pixel-level Mask
  ↓
Mask Postprocess / Quality Report
  ↓
Diffusers Inpaint / Video Tracking / 可视化输出
```

SAM 2 是 Meta 发布的图像与视频统一分割模型，支持用点、框、mask 等 prompt 选择目标对象，并且扩展到视频目标追踪场景；官方 SAM 2 仓库已经发布 SAM 2.1 checkpoint，使用 SAM 2.1 权重时需要保持代码为最新版本。

------

## 1. 工程化目录架构

推荐项目名：

```
04_sam2-vision-segmentation-lab
```

目录树：

```
04_sam2-vision-segmentation-lab/
├── Makefile
├── README.md
├── Week04_runbook.md
├── requirements.txt
├── pyproject.toml
├── .gitignore
├── .env.example
│
├── configs/
│   ├── sam2.yaml
│   ├── inpaint.yaml
│   ├── app.yaml
│   └── logging.yaml
│
├── models/
│   ├── sam2/
│   │   └── checkpoints/
│   └── diffusers/
│
├── data/
│   ├── images/
│   │   ├── sample_01.jpg
│   │   ├── sample_02.jpg
│   │   └── sample_03.jpg
│   ├── videos/
│   │   └── sample_video.mp4
│   └── masks/
│
├── outputs/
│   ├── masks/
│   ├── overlays/
│   ├── inpaint/
│   ├── video/
│   ├── reports/
│   └── manifests/
│
├── scripts/
│   ├── 00_check_env.py
│   ├── 01_download_sam2.py
│   ├── 02_segment_point.py
│   ├── 03_segment_box.py
│   ├── 04_segment_auto.py
│   ├── 05_mask_quality_report.py
│   ├── 06_sam2_inpaint.py
│   ├── 07_video_track.py
│   └── 99_smoke_test.py
│
├── src/
│   └── sam2_lab/
│       ├── __init__.py
│       ├── app.py
│       ├── config.py
│       ├── device.py
│       ├── logging_utils.py
│       │
│       ├── sam/
│       │   ├── loader.py
│       │   ├── image_predictor.py
│       │   ├── auto_mask.py
│       │   └── video_predictor.py
│       │
│       ├── mask/
│       │   ├── postprocess.py
│       │   ├── quality.py
│       │   ├── geometry.py
│       │   └── visualize.py
│       │
│       ├── inpaint/
│       │   ├── pipeline.py
│       │   └── runner.py
│       │
│       ├── api/
│       │   ├── server.py
│       │   ├── schemas.py
│       │   └── routes.py
│       │
│       └── utils/
│           ├── image_io.py
│           ├── manifest.py
│           └── timer.py
│
├── notebooks/
│   └── sam2_segmentation_demo.ipynb
│
├── tests/
│   ├── test_device.py
│   ├── test_mask_postprocess.py
│   ├── test_quality_report.py
│   ├── test_manifest.py
│   └── test_api_contract.py
│
└── docs/
    ├── architecture.md
    ├── model_cards.md
    ├── mask_quality_metrics.md
    ├── failure_cases.md
    └── interview_notes.md
```

目录职责：

| 目录            | 作用                                                         |
| --------------- | ------------------------------------------------------------ |
| `configs/`      | 管理 SAM 2、Diffusers Inpaint、API 服务和日志配置，避免硬编码参数。 |
| `models/`       | 本地模型权重目录，不提交 GitHub，只保留 `.gitkeep`。         |
| `data/`         | 放置演示图片、视频、输入 mask，便于复现实验。                |
| `outputs/`      | 保存 mask、overlay、inpaint 结果、视频结果和 manifest。      |
| `scripts/`      | 面向学习和调试的单步脚本，每个脚本对应一个实验目标。         |
| `src/sam2_lab/` | 正式工程代码，供 CLI、API、测试共同调用。                    |
| `notebooks/`    | 教学型 Notebook，展示 Point / Box / Auto 三种分割。          |
| `tests/`        | 单元测试与契约测试，保证后处理、质量报告、manifest 可复现。  |
| `docs/`         | 面试复盘、架构图、失败案例、指标定义文档。                   |
| `Makefile`      | 统一封装安装、下载、运行、测试、清理、服务管理。             |

------

## 2. 依赖安装与最新工具链配置

### 2.1 激活 Conda 环境

本项目只使用 Conda 环境 `cxllm`，不使用 `venv`。

```
conda activate cxllm
python --version
which python
```

预期：

```
Python 3.11.x
.../anaconda3/envs/cxllm/bin/python
```

------

### 2.2 安装基础依赖

官方 SAM 2 仓库要求 Python `>=3.10`，并建议先安装 PyTorch 与 TorchVision；官方安装文档也说明可以通过 `SAM2_BUILD_CUDA=0` 跳过 CUDA 扩展，这对 macOS Apple Silicon 很关键，因为本机没有 CUDA。

```
python -m pip install -U pip setuptools wheel
python -m pip install -U \
  torch torchvision torchaudio \
  numpy opencv-python pillow matplotlib scipy \
  pydantic pydantic-settings pyyaml \
  fastapi uvicorn python-multipart \
  gradio \
  pytest pytest-cov ruff mypy \
  huggingface_hub hf_xet \
  diffusers transformers accelerate safetensors
```

Apple Silicon 使用 PyTorch 的 MPS 后端，MPS 通过 Metal 调用 Apple GPU；Diffusers 官方也明确支持将 pipeline `.to("mps")`，并建议内存小于 64GB 的设备启用 attention slicing。

------

### 2.3 安装 SAM 2

推荐直接从官方 GitHub 安装最新代码，保证 SAM 2.1 checkpoint 能正确加载。

```
mkdir -p external
cd external

git clone https://github.com/facebookresearch/sam2.git
cd sam2

# macOS / Apple Silicon：跳过 CUDA extension
SAM2_BUILD_CUDA=0 python -m pip install -e ".[notebooks]"

cd ../..
```

检查安装：

```
python - <<'PY'
import torch
import sam2
print("torch:", torch.__version__)
print("mps available:", torch.backends.mps.is_available())
print("sam2 import ok")
PY
```

预期：

```
torch: 2.x.x
mps available: True
sam2 import ok
```

如果看到类似：

```
Failed to build the SAM 2 CUDA extension
```

在 macOS 上可以忽略。官方文档说明 CUDA 扩展失败或跳过时，主要影响部分 CUDA 后处理，不影响绝大多数图像与视频分割结果。

------

### 2.4 配置 Hugging Face 国内镜像

Hugging Face 官方工具链支持通过环境变量配置本地缓存目录、token、Hub cache 等；国内下载可使用 `HF_ENDPOINT` 指向 `hf-mirror.com`，HF-Mirror 页面也明确给出 `export HF_ENDPOINT=https://hf-mirror.com` 的用法。

```
export HF_ENDPOINT=https://hf-mirror.com
export HF_HOME="$PWD/.cache/huggingface"
export HF_HUB_CACHE="$PWD/.cache/huggingface/hub"
export HF_XET_HIGH_PERFORMANCE=1
```

建议写入项目级 `.env`：

```
cat > .env.example <<'EOF'
HF_ENDPOINT=https://hf-mirror.com
HF_HOME=.cache/huggingface
HF_HUB_CACHE=.cache/huggingface/hub
HF_XET_HIGH_PERFORMANCE=1
SAM2_MODEL_SIZE=tiny
SAM2_DEVICE=auto
API_HOST=127.0.0.1
API_PORT=8004
GRADIO_PORT=7864
EOF
```

------

### 2.5 模型下载策略

SAM 2.1 官方 checkpoint 包含 tiny、small、base_plus、large 四档；官方仓库列出了 `sam2.1_hiera_tiny.pt`、`sam2.1_hiera_small.pt`、`sam2.1_hiera_base_plus.pt`、`sam2.1_hiera_large.pt`。

对 MacBook Air M5 / 32GB 统一内存，建议：

| 模型                        | 推荐程度 | 理由                                                   |
| --------------------------- | -------- | ------------------------------------------------------ |
| `sam2.1_hiera_tiny.pt`      | ⭐⭐⭐⭐⭐    | 入门首选，速度快，适合 Point / Box / Auto / API Demo。 |
| `sam2.1_hiera_small.pt`     | ⭐⭐⭐⭐     | 质量更好，仍然适合 32GB 统一内存。                     |
| `sam2.1_hiera_base_plus.pt` | ⭐⭐⭐      | 可试，但全图自动分割和视频追踪会变慢。                 |
| `sam2.1_hiera_large.pt`     | ⭐⭐       | 可加载风险高，速度慢，不建议作为默认开源配置。         |

01_download_sam2.py代码文件配置

```
#!/usr/bin/env python3
"""
SAM 2 Checkpoint 下载脚本
用于自动下载 Meta 官方发布的 SAM 2.1 权重文件。
"""

import argparse
import os
import sys
import urllib.request

# SAM 2.1 官方直链
SAM2_1_URLS = {
    "tiny": "https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_tiny.pt",
    "small": "https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_small.pt",
    "base_plus": "https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_base_plus.pt",
    "large": "https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_large.pt"
}

def download_progress(count, block_size, total_size):
    """终端下载进度条回调函数"""
    if total_size > 0:
        percent = min(100, int(count * block_size * 100 / total_size))
        downloaded_mb = (count * block_size) / (1024 * 1024)
        total_mb = total_size / (1024 * 1024)
        sys.stdout.write(f"\r下载进度: {percent}% [{downloaded_mb:.2f} MB / {total_mb:.2f} MB]")
        sys.stdout.flush()

def main():
    parser = argparse.ArgumentParser(description="下载 SAM 2.1 模型权重文件")
    parser.add_argument(
        "--model-size", 
        type=str, 
        default="tiny", 
        choices=SAM2_1_URLS.keys(), 
        help="指定要下载的模型大小档位"
    )
    parser.add_argument(
        "--output-dir", 
        type=str, 
        default="models/sam2/checkpoints", 
        help="权重文件保存目录"
    )
    args = parser.parse_args()

    url = SAM2_1_URLS[args.model_size]
    filename = url.split("/")[-1]
    output_path = os.path.join(args.output_dir, filename)

    # 确保输出目录存在
    os.makedirs(args.output_dir, exist_ok=True)

    # 检查是否已存在，避免重复下载
    if os.path.exists(output_path):
        print(f"✅ 文件已存在，跳过下载: {output_path}")
        return

    print(f"🚀 开始下载 SAM 2.1 ({args.model_size}) 模型...")
    print(f"🔗 来源: {url}")
    print(f"📁 目标: {output_path}")
    
    try:
        urllib.request.urlretrieve(url, output_path, reporthook=download_progress)
        print(f"\n✅ 成功下载到: {output_path}")
    except Exception as e:
        print(f"\n❌ 下载失败: {e}")
        print("建议检查网络连通性，或使用 runbook 中提供的 curl 命令兜底下载。")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

推荐默认下载 tiny：

```
mkdir -p models/sam2/checkpoints

python scripts/01_download_sam2.py \
  --model-size tiny \
  --output-dir models/sam2/checkpoints
```

如果脚本下载失败，可以使用官方直链兜底：

```
curl -L \
  -o models/sam2/checkpoints/sam2.1_hiera_tiny.pt \
  https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_tiny.pt
```

> 注意：SAM 2 官方 checkpoint 不一定全部以标准 Hugging Face repo 形式托管。Diffusers Inpaint 模型可以走 `hf download` + `HF_ENDPOINT`，SAM 2 checkpoint 优先使用官方 checkpoint URL 或脚本兜底。

Diffusers Inpaint 模型下载：

```
export HF_ENDPOINT=https://hf-mirror.com

hf download runwayml/stable-diffusion-inpainting \
  --local-dir models/diffusers/stable-diffusion-inpainting \
  --include "*.json" "*.txt" "*.safetensors" "*.bin" \
  --local-dir-use-symlinks False
```

------

## 3. 配置文件

### 3.1 `configs/sam2.yaml`

```
model:
  size: tiny
  checkpoint: models/sam2/checkpoints/sam2.1_hiera_tiny.pt
  config: configs/sam2.1/sam2.1_hiera_t.yaml
  device: auto

image:
  max_long_side: 1024
  default_multimask_output: true

auto_mask:
  points_per_side: 32
  pred_iou_thresh: 0.88
  stability_score_thresh: 0.92
  min_mask_region_area: 500

postprocess:
  min_area: 500
  morph_kernel_size: 5
  fill_holes: true
  smooth_contour: true

output:
  masks_dir: outputs/masks
  overlays_dir: outputs/overlays
  reports_dir: outputs/reports
  manifests_dir: outputs/manifests
```

------

### 3.2 `configs/inpaint.yaml`

```
model:
  repo_or_path: models/diffusers/stable-diffusion-inpainting
  fallback_repo: runwayml/stable-diffusion-inpainting
  device: auto

generation:
  prompt: "a beautiful clean product design background, studio lighting"
  negative_prompt: "low quality, blurry, watermark, distorted"
  steps: 25
  guidance_scale: 7.5
  width: 512
  height: 512
  seed: 42

mps:
  torch_dtype: float32
  attention_slicing: true
```

------

### 3.3 `configs/app.yaml`

```
api:
  host: 127.0.0.1
  port: 8004

gradio:
  host: 127.0.0.1
  port: 7864

logging:
  level: INFO
```

------

## 4. 关键源码骨架

### 4.1 `src/sam2_lab/device.py`

```
from __future__ import annotations

import torch


def get_device(preferred: str = "auto") -> str:
    if preferred != "auto":
        return preferred

    if torch.backends.mps.is_available():
        return "mps"

    if torch.cuda.is_available():
        return "cuda"

    return "cpu"


def get_torch_dtype(device: str):
    if device == "cuda":
        return torch.float16

    # MPS 对部分 float16 / bfloat16 算子支持仍可能不完整，学习项目默认 float32 更稳。
    if device == "mps":
        return torch.float32

    return torch.float32
```

------

### 4.2 `src/sam2_lab/mask/postprocess.py`

```
from __future__ import annotations

import cv2
import numpy as np


def postprocess_mask(
    mask: np.ndarray,
    min_area: int = 500,
    kernel_size: int = 5,
) -> np.ndarray:
    """二值化、去噪、填孔、连通域过滤。"""
    if mask.dtype != np.bool_:
        mask = mask > 0

    mask_u8 = (mask.astype(np.uint8) * 255)

    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        (kernel_size, kernel_size),
    )

    opened = cv2.morphologyEx(mask_u8, cv2.MORPH_OPEN, kernel)
    closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel)

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(closed)
    result = np.zeros_like(closed)

    for idx in range(1, num_labels):
        area = stats[idx, cv2.CC_STAT_AREA]
        if area >= min_area:
            result[labels == idx] = 255

    return result > 0
```

------

### 4.3 `src/sam2_lab/mask/quality.py`

```
from __future__ import annotations

import cv2
import numpy as np


def mask_quality_report(mask: np.ndarray) -> dict:
    """生成 mask 质量报告：面积、连通域、孔洞、边缘复杂度。"""
    if mask.dtype != np.bool_:
        mask = mask > 0

    mask_u8 = (mask.astype(np.uint8) * 255)

    contours, hierarchy = cv2.findContours(
        mask_u8,
        cv2.RETR_CCOMP,
        cv2.CHAIN_APPROX_SIMPLE,
    )

    external_contours, _ = cv2.findContours(
        mask_u8,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )

    connected_count, _, stats, _ = cv2.connectedComponentsWithStats(mask_u8)

    areas = [
        int(stats[i, cv2.CC_STAT_AREA])
        for i in range(1, connected_count)
    ]

    largest_area = max(areas) if areas else 0
    total_area = int(mask.sum())

    hole_count = 0
    if hierarchy is not None:
        for h in hierarchy[0]:
            parent = h[3]
            if parent != -1:
                hole_count += 1

    edge_points = sum(len(c) for c in external_contours)

    return {
        "area_px": total_area,
        "connected_components": max(connected_count - 1, 0),
        "largest_component_area_px": largest_area,
        "hole_count": hole_count,
        "edge_points": int(edge_points),
        "largest_area_ratio": round(largest_area / total_area, 4) if total_area else 0,
    }
```

------

### 4.4 `src/sam2_lab/utils/manifest.py`

```
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def append_manifest(path: str | Path, record: dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        **record,
    }

    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")
```

------

## 5. 分终端执行与测试流程

### 5.1 终端 0：初始化项目

.Makefile内容

```
.PHONY: setup check-env

setup:
	@echo "[setup] Python:"
	@python --version
	@echo "[setup] Installing Python dependencies..."
	@python -m pip install -U pip setuptools wheel
	@python -m pip install -U torch torchvision torchaudio numpy opencv-python pillow matplotlib scipy pydantic pydantic-settings pyyaml fastapi uvicorn python-multipart gradio pytest pytest-cov ruff mypy huggingface_hub hf_xet diffusers transformers accelerate safetensors
	@echo "[setup] Installing SAM 2 from source..."
	@if [ -d "external/sam2" ]; then \
		cd external/sam2 && SAM2_BUILD_CUDA=0 python -m pip install -e ".[notebooks]"; \
	else \
		echo "sam2 源码不存在，请先执行 runbook 中的 git clone 步骤"; \
	fi
	@echo "[setup] Done."

check-env:
	@python -c '\
import torch; \
print("device=mps"); \
print("torch.backends.mps.is_available=" + str(torch.backends.mps.is_available())); \
import sam2; print("sam2 import ok"); \
import cv2; print("opencv import ok"); \
import diffusers; print("diffusers import ok")'
```



```
conda activate cxllm

mkdir -p 04_sam2-vision-segmentation-lab
cd 04_sam2-vision-segmentation-lab

mkdir -p \
  configs models/sam2/checkpoints models/diffusers \
  data/images data/videos data/masks \
  outputs/masks outputs/overlays outputs/inpaint outputs/video outputs/reports outputs/manifests \
  scripts src/sam2_lab tests docs notebooks external
  
```

------

### 5.2 终端 1：安装依赖

```
conda activate cxllm
cd 04_sam2-vision-segmentation-lab

make setup
```

预期看到：

```
[setup] Python:
Python 3.11.x
[setup] Installing Python dependencies...
[setup] Installing SAM 2 from source...
[setup] Done.
```

检查环境：

```
make check-env
```

预期看到：

```
device=mps
torch.backends.mps.is_available=True
sam2 import ok
opencv import ok
diffusers import ok
```

------

### 5.3 终端 2：下载模型

```
conda activate cxllm
cd 04_sam2-vision-segmentation-lab

make download-models
```

预期看到：

```
[download] SAM2 checkpoint exists: models/sam2/checkpoints/sam2.1_hiera_tiny.pt
[download] Diffusers inpaint model ready
```

如果 HF 下载速度慢：

```
export HF_ENDPOINT=https://hf-mirror.com
export HF_XET_HIGH_PERFORMANCE=1
make download-diffusers
```

------

### 5.4 终端 3：运行 Point Prompt 分割

准备一张图片：

```
cp /path/to/your/photo.jpg data/images/sample_01.jpg
```

写入scripts/02_segment_point.py代码

```
import argparse
import os
import cv2
import numpy as np
import torch
import json
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
```

执行：

```
make segment-point IMAGE=data/images/sample_01.jpg X=400 Y=300
```

预期输出：

```
[segment-point] image=data/images/sample_01.jpg
[segment-point] point=(400,300), label=1
[segment-point] best_score=0.94
[segment-point] mask saved: outputs/masks/sample_01_point_mask.png
[segment-point] overlay saved: outputs/overlays/sample_01_point_overlay.png
[segment-point] manifest appended: outputs/manifests/segmentation_manifest.jsonl
```

------

### 5.5 终端 3：运行 Box Prompt 分割

写入scripts/03_segment_box.py代码文件

```
import argparse
import os
import cv2
import numpy as np
import torch
import json
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
```



```
make segment-box \
  IMAGE=data/images/sample_01.jpg \
  X1=100 Y1=80 X2=700 Y2=600
```

预期输出：

```
[segment-box] box=[100,80,700,600]
[segment-box] mask saved: outputs/masks/sample_01_box_mask.png
[segment-box] quality report saved: outputs/reports/sample_01_box_quality.json
```

------

### 5.6 终端 3：运行全图自动分割 

写入`scripts/04_segment_auto.py`代码文件

```
import argparse
import os
import cv2
import numpy as np
import torch
import json
from sam2.build_sam import build_sam2
from sam2.automatic_mask_generator import SAM2AutomaticMaskGenerator

def main():
    parser = argparse.ArgumentParser(description="SAM 2 Auto Segmentation")
    parser.add_argument("--image", required=True, help="输入图片路径")
    args = parser.parse_args()

    # MPS 对底层大量并发矩阵运算支持较好
    device = "mps" if torch.backends.mps.is_available() else "cpu"

    checkpoint = "models/sam2/checkpoints/sam2.1_hiera_tiny.pt"
    model_cfg = "configs/sam2.1/sam2.1_hiera_t.yaml"
    
    model = build_sam2(model_cfg, checkpoint, device=device)
    # 使用自动掩码生成器
    mask_generator = SAM2AutomaticMaskGenerator(model)

    image_bgr = cv2.imread(args.image)
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

    print(f"🚀 正在对 {args.image} 进行全图自动分割，这需要一点时间...")
    masks = mask_generator.generate(image_rgb)
    print(f"[segment-auto] detected_masks={len(masks)}")

    os.makedirs("outputs/reports", exist_ok=True)
    os.makedirs("outputs/masks", exist_ok=True)
    base_name = os.path.splitext(os.path.basename(args.image))[0]

    # 按面积大小排序，取前10个最大的Mask进行导出演示
    masks = sorted(masks, key=(lambda x: x['area']), reverse=True)
    top_masks = masks[:10]
    
    report_data = {"total_detected": len(masks), "top_10_areas": []}

    for i, mask_data in enumerate(top_masks):
        mask_bool = mask_data['segmentation']
        mask_u8 = (mask_bool * 255).astype(np.uint8)
        mask_path = f"outputs/masks/{base_name}_auto_{i}.png"
        cv2.imwrite(mask_path, mask_u8)
        report_data["top_10_areas"].append({"index": i, "area": mask_data['area']})

    print("[segment-auto] top10 masks exported")
    
    report_path = f"outputs/reports/{base_name}_auto_masks.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)
    print(f"[segment-auto] report saved: {report_path}")

if __name__ == "__main__":
    main()
```

运行

```
make segment-auto IMAGE=data/images/sample_01.jpg
```

预期输出：

```
[segment-auto] detected_masks=xx
[segment-auto] top10 masks exported
[segment-auto] report saved: outputs/reports/sample_01_auto_masks.json
```

全图自动分割会比 Point / Box 慢很多。如果图片太大，先压到最长边 1024：

```
python scripts/resize_image.py \
  --input data/images/sample_01.jpg \
  --output data/images/sample_01_1024.jpg \
  --max-long-side 1024
```

------

### 5.7 终端 4：启动 API 服务

写入src/sam2_lab/api/server.py代码文件：

```
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
import torch
import cv2
import numpy as np
from sam2.build_sam import build_sam2
from sam2.sam2_image_predictor import SAM2ImagePredictor

app = FastAPI(title="SAM 2 Vision API")

# 全局变量存放模型，避免每次请求都重新加载
predictor = None
device = "mps" if torch.backends.mps.is_available() else "cpu"

@app.on_event("startup")
async def startup_event():
    global predictor
    print("INFO: Loading SAM2 model...")
    checkpoint = "models/sam2/checkpoints/sam2.1_hiera_tiny.pt"
    model_cfg = "configs/sam2.1/sam2.1_hiera_t.yaml"
    model = build_sam2(model_cfg, checkpoint, device=device)
    predictor = SAM2ImagePredictor(model)
    print(f"INFO: SAM2 loaded: {checkpoint} on {device}")

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "device": device,
        "model": "sam2.1_hiera_tiny"
    }

@app.post("/segment/point")
async def segment_point(
    image: UploadFile = File(...),
    x: int = Form(...),
    y: int = Form(...),
    label: int = Form(1)
):
    # 读取上传的图片流并转换为 OpenCV 格式
    contents = await image.read()
    nparr = np.frombuffer(contents, np.uint8)
    img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

    predictor.set_image(img_rgb)
    input_point = np.array([[x, y]])
    input_label = np.array([label])

    masks, scores, _ = predictor.predict(
        point_coords=input_point, point_labels=input_label, multimask_output=True
    )
    
    best_idx = np.argmax(scores)
    best_score = float(scores[best_idx])
    # API 通常返回处理后的数据或坐标，这里做简化示例，返回得分和状态
    return JSONResponse(content={"status": "success", "best_score": best_score, "point": [x, y]})

@app.post("/segment/box")
async def segment_box(
    image: UploadFile = File(...),
    x1: int = Form(...), y1: int = Form(...),
    x2: int = Form(...), y2: int = Form(...)
):
    contents = await image.read()
    nparr = np.frombuffer(contents, np.uint8)
    img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

    predictor.set_image(img_rgb)
    input_box = np.array([[x1, y1, x2, y2]])

    masks, scores, _ = predictor.predict(
        point_coords=None, point_labels=None, box=input_box, multimask_output=True
    )
    
    best_idx = np.argmax(scores)
    return JSONResponse(content={"status": "success", "best_score": float(scores[best_idx]), "box": [x1, y1, x2, y2]})
```



```
conda activate cxllm
cd 04_sam2-vision-segmentation-lab

make api
```

预期日志：

```
INFO:     Uvicorn running on http://127.0.0.1:8004
INFO:     SAM2 loaded: sam2.1_hiera_tiny.pt
INFO:     device=mps
```

------

### 5.8 终端 5：Curl 调试 API

健康检查：

```
curl http://127.0.0.1:8004/health
```

预期：

```
{
  "status": "ok",
  "device": "mps",
  "model": "sam2.1_hiera_tiny"
}
```

Point 分割请求：

```
curl -X POST http://127.0.0.1:8004/segment/point \
  -F "image=@data/images/sample_01.jpg" \
  -F "x=400" \
  -F "y=300" \
  -F "label=1" \
  -o outputs/api_point_result.json
```

Box 分割请求：

```
curl -X POST http://127.0.0.1:8004/segment/box \
  -F "image=@data/images/sample_01.jpg" \
  -F "x1=100" \
  -F "y1=80" \
  -F "x2=700" \
  -F "y2=600" \
  -o outputs/api_box_result.json
```

------

### 5.9 终端 6：SAM 2 + Diffusers Inpaint

写入scripts/06_sam2_inpaint.py代码文件

```
import argparse
import os
import torch
from PIL import Image
from diffusers import StableDiffusionInpaintPipeline

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True, help="原始图片路径")
    parser.add_argument("--mask", required=True, help="SAM 2 抠出的黑白 Mask 路径")
    parser.add_argument("--prompt", required=True, help="生成提示词")
    args = parser.parse_args()

    print("[inpaint] loading StableDiffusionInpaintPipeline")
    # 指向你之前通过 make download-diffusers 缓存在本地的模型
    model_id = "models/diffusers/stable-diffusion-inpainting"
    
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    
    # 针对 Mac 架构的防御性配置
    pipe = StableDiffusionInpaintPipeline.from_pretrained(
        model_id, 
        torch_dtype=torch.float32, 
        local_files_only=True,
        safety_checker=None # 纯本地学习环境可以关闭安全检查器提升速度
    ).to(device)
    
    pipe.enable_attention_slicing()
    print(f"[inpaint] device={device} dtype=float32 attention_slicing=True")

    # PIL 读取原图和遮罩，需调整为 512x512 以匹配基础 SD 模型的最佳分辨率
    init_image = Image.open(args.image).convert("RGB").resize((512, 512))
    mask_image = Image.open(args.mask).convert("RGB").resize((512, 512))

    print(f"🎨 开始基于 Prompt 重绘区域: {args.prompt}")
    # 执行 Inpaint 生成
    output = pipe(
        prompt=args.prompt,
        image=init_image,
        mask_image=mask_image,
        num_inference_steps=25,
        guidance_scale=7.5
    ).images[0]

    os.makedirs("outputs/inpaint", exist_ok=True)
    base_name = os.path.splitext(os.path.basename(args.image))[0]
    out_path = f"outputs/inpaint/{base_name}_inpaint.png"
    
    output.save(out_path)
    print(f"[inpaint] output saved: {out_path}")

if __name__ == "__main__":
    main()
```

执行：

```
make inpaint \
  IMAGE=data/images/sample_01.jpg \
  MASK=outputs/masks/sample_01_point_mask.png \
  PROMPT="a clean futuristic product design background, soft studio lighting"
```

预期：

```
[inpaint] loading StableDiffusionInpaintPipeline
[inpaint] device=mps dtype=float32 attention_slicing=True
[inpaint] output saved: outputs/inpaint/sample_01_inpaint.png
```

在 MPS 上 Diffusers Inpaint 速度不会像 CUDA 那么快，默认使用 `float32` 与 `enable_attention_slicing()`，优先保证稳定。

------

### 5.10 终端 7：运行测试

```
make test
```

预期：

```
tests/test_device.py ...
tests/test_mask_postprocess.py ...
tests/test_quality_report.py ...
tests/test_manifest.py ...
tests/test_api_contract.py ...
```

------

### 5.11 终端 8：视频目标追踪

SAM 2 的杀手级功能——在视频首帧点击目标，自动追踪该目标在所有帧中的 mask。

```bash
python scripts/07_video_track.py \
  --video data/videos/sample_video.mp4 \
  --x 300 --y 250 \
  --frame-idx 0
```

或使用 Makefile：

```bash
make video-track X=300 Y=250
```

**参数说明：**

| 参数 | 默认值 | 含义 |
|------|--------|------|
| `--video` | `data/videos/sample_video.mp4` | 输入视频路径 |
| `--x`, `--y` | Makefile 默认 400/300 | 首帧点击坐标 |
| `--frame-idx` | 0 | 添加 prompt 的帧索引 |
| `--label` | 1 | 1=前景, 0=背景 |
| `--vis-frame-stride` | 5 | 每隔多少帧保存一张可视化叠加图 |

**内部流程：**

```
1. build_sam2_video_predictor(config, checkpoint, device)
2. predictor.init_state(video_path)
   → 读取所有帧 + 提取 Frame 0 图像特征
3. predictor.add_new_points_or_box(frame_idx=0, obj_id=1, points, labels)
   → 在首帧注册追踪目标
4. predictor.propagate_in_video(inference_state)
   → 逐帧传播 mask（Memory Attention 机制）
5. 遍历所有帧，调用 _get_orig_video_res_output() 导出 mask
6. 保存 mask PNG + overlay PNG + JSONL manifest
```

**预期输出：**

```
[video-track] 设备: mps
[video-track] 视频: data/videos/sample_video.mp4
[video-track] 追踪点: (300, 250)  @ frame 0
[video-track] 正在加载 SAM 2 视频预测器...
[video-track] 模型加载完成 ✓
[video-track] 正在初始化视频推理状态（提取帧 + 编码特征）...
[video-track] 视频信息: 60 帧, 1920x1080
[video-track] 在 frame 0 添加 prompt...
[video-track] 已注册追踪目标 ID: [1] ✓
[video-track] 正在将 mask 传播到所有帧（这可能需要一些时间）...
  [video-track] 处理进度: 1/60 帧
  [video-track] 处理进度: 31/60 帧
[video-track] 视频传播完成 ✓

============================================================
[video-track] ✅ 视频追踪完成!
[video-track] 总帧数:     60
[video-track] 保存 mask 数: 60
[video-track] mask 目录:    outputs/video/sample_video_frames
[video-track] manifest:     outputs/video/sample_video_manifest.jsonl
============================================================
```

**输出产物：**
- `outputs/video/sample_video_frames/*.png` — 每帧的 mask
- `outputs/video/sample_video_frames/*_overlay.png` — 每 5 帧的可视化叠加
- `outputs/video/sample_video_manifest.jsonl` — 逐帧 mask 面积记录

**Python API 等效代码：**

```python
from sam2_lab.sam.video_predictor import VideoTracker

tracker = VideoTracker()
tracker.init_video("data/videos/sample_video.mp4")
tracker.add_prompt(frame_idx=0, points=[(300, 250)], labels=[1])
tracker.propagate()
mask_frame_0 = tracker.get_mask(0)
```

**注意事项：**
- 视频追踪需要较大内存（加载全部帧到内存），32GB 统一内存建议视频 ≤ 200 帧
- 如果目标短暂被遮挡，SAM 2 的 Memory Bank 通常能保持追踪
- 如果追踪漂移，可以多点几个关键帧做 correction

------

### 5.12 终端 9：Mask 质量报告 CLI

独立的 CLI 工具，读取任意 mask PNG 文件并输出 JSON 质量报告。

```bash
# 输出到 stdout
python scripts/05_mask_quality_report.py \
  --mask outputs/masks/sample_01_point_mask.png

# 输出到文件
python scripts/05_mask_quality_report.py \
  --mask outputs/masks/sample_01_point_mask.png \
  --output outputs/reports/sample_01_quality.json
```

或使用 Makefile：

```bash
make quality MASK=outputs/masks/sample_01_point_mask.png
```

**预期输出：**

```json
{
  "area_px": 36057,
  "connected_components": 1,
  "largest_component_area_px": 36057,
  "hole_count": 0,
  "edge_points": 423,
  "largest_area_ratio": 1.0,
  "source_mask": "/path/to/sample_01_point_mask.png"
}
```

**质量指标解读：**

| 指标 | 含义 | 评价 |
|------|------|------|
| `area_px` | 前景像素总数 | — |
| `connected_components` | 连通域数 | 1=最佳（物体完整） |
| `hole_count` | 内部孔洞数 | 0=最佳 |
| `edge_points` | 轮廓点数 | 越少越平滑 |
| `largest_area_ratio` | 最大连通域占比 | >0.95=优秀 |

------

### 5.13 终端 10：环境自检

运行 14 项自动化检查，确认开发环境就绪。

```bash
python scripts/00_check_env.py
# 或
make check-env
```

**检查项：**
1. Python >= 3.11
2. PyTorch + MPS/CUDA
3. opencv-python, numpy, Pillow, PyYAML
4. SAM 2 (build_sam2)
5. SAM 2 checkpoint 文件
6. Diffusers + Transformers
7. FastAPI + Uvicorn + Gradio
8. 项目自身包 (sam2_lab)

**预期输出：**

```
=======================================================
  SAM 2 Vision Segmentation Lab — 环境自检
=======================================================

🔍 1. Python 版本
  ✅ Python 3.13.13

🔍 2. PyTorch + 加速后端
  ✅ PyTorch 2.12.0 (MPS 可用)

...

=======================================================
  ✅ 全部 14 项检查通过！环境就绪。
=======================================================
```

------

### 5.14 终端 11：冒烟测试

快速端到端验证核心链路：模块导入 → Point 分割 → API 健康检查。

```bash
python scripts/99_smoke_test.py
# 或
make smoke
```

**预期输出：**

```
=======================================================
  SAM 2 Lab — 冒烟测试
=======================================================

🧪 1. 核心模块导入
  ✅ import sam2_lab.device
  ✅ import sam2_lab.mask.postprocess
  ✅ import sam2_lab.mask.quality
  ✅ import sam2_lab.utils.manifest

🧪 2. Point 分割端到端
  ✅ Point 分割成功 — best_score=0.878, mask_area=36057px
  ✅ smoke_test_mask 已保存

🧪 3. FastAPI 健康检查
  ✅ API /health 响应 — status=ok, device=mps

=======================================================
  ✅ 冒烟测试全部通过 (3/3)
=======================================================
```

------

### 5.15 终端 12：Gradio Web UI

启动拖拽式交互界面，在浏览器中完成 Point/Box/Inpaint 全流程。

```bash
PYTHONPATH=src python -m sam2_lab.app
# 或
make ui
```

**访问：** http://127.0.0.1:7864

**三个 Tab：**

| Tab | 功能 | 操作方式 |
|-----|------|----------|
| 🎯 Point 分割 | 点击图片 → 自动分割 | 拖入图片 + 点击目标位置 |
| 📦 Box 分割 | 滑块框选 → 分割 | 拖入图片 + 调整 4 个滑块 |
| 🎨 Inpaint 修复 | 分割 + AI 背景替换 | 拖入图片 + 点击物体 + 输入提示词 |

**交互亮点：**
- 点击图片自动获取坐标（无需手动输数字）
- 分割结果实时显示 mask + overlay 双视图
- Inpaint Tab 一键完成 SAM2→Diffusers 全链路

**启动时模型懒加载**：首次操作时才加载 SAM2/Inpaint 模型，避免 UI 启动时长时间等待。

**预期启动日志：**

```
=======================================================
  SAM 2 Vision Lab — Gradio UI
  地址: http://127.0.0.1:7864
=======================================================

* Running on local URL:  http://127.0.0.1:7864
```

------

## 6. 终极一键运行：Makefile 集成

下面这份 `Makefile` 可以直接放到项目根目录。

```
SHELL := /bin/bash

PROJECT_NAME := 04_sam2-vision-segmentation-lab
PYTHON := python
PIP := python -m pip

API_HOST ?= 127.0.0.1
API_PORT ?= 8004
GRADIO_PORT ?= 7864

IMAGE ?= data/images/sample_01.jpg
MASK ?= outputs/masks/sample_01_point_mask.png

X ?= 400
Y ?= 300
LABEL ?= 1

X1 ?= 100
Y1 ?= 80
X2 ?= 700
Y2 ?= 600

PROMPT ?= a clean futuristic product design background, soft studio lighting

HF_ENDPOINT ?= https://hf-mirror.com
HF_HOME ?= $(PWD)/.cache/huggingface
HF_HUB_CACHE ?= $(PWD)/.cache/huggingface/hub
HF_XET_HIGH_PERFORMANCE ?= 1

SAM2_REPO := external/sam2
SAM2_CKPT_DIR := models/sam2/checkpoints
SAM2_TINY_CKPT := $(SAM2_CKPT_DIR)/sam2.1_hiera_tiny.pt
SAM2_TINY_URL := https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_tiny.pt

.PHONY: help
help:
	@echo ""
	@echo "$(PROJECT_NAME) commands:"
	@echo "  make setup              Install dependencies and SAM2"
	@echo "  make check-env          Check Python/PyTorch/MPS/SAM2"
	@echo "  make download-models    Download SAM2 + Diffusers models"
	@echo "  make api                Start FastAPI service"
	@echo "  make ui                 Start Gradio UI"
	@echo "  make run-all            Start API + UI with nohup"
	@echo "  make stop               Stop background services"
	@echo "  make segment-point      Run point prompt segmentation"
	@echo "  make segment-box        Run box prompt segmentation"
	@echo "  make segment-auto       Run automatic mask generation"
	@echo "  make inpaint            Run SAM2 mask + Diffusers inpaint"
	@echo "  make video-track        Run SAM2 video tracking demo"
	@echo "  make test               Run tests"
	@echo "  make lint               Run ruff"
	@echo "  make clean              Clean outputs/cache"
	@echo ""

.PHONY: setup
setup:
	@echo "[setup] Python:"
	@$(PYTHON) --version
	@echo "[setup] Installing base dependencies..."
	@$(PIP) install -U pip setuptools wheel
	@$(PIP) install -r requirements.txt
	@echo "[setup] Installing SAM2..."
	@mkdir -p external
	@if [ ! -d "$(SAM2_REPO)" ]; then \
		git clone https://github.com/facebookresearch/sam2.git $(SAM2_REPO); \
	else \
		cd $(SAM2_REPO) && git pull; \
	fi
	@cd $(SAM2_REPO) && SAM2_BUILD_CUDA=0 $(PIP) install -e ".[notebooks]"
	@echo "[setup] Done."

.PHONY: check-env
check-env:
	@$(PYTHON) scripts/00_check_env.py

.PHONY: download-models
download-models: download-sam2 download-diffusers

.PHONY: download-sam2
download-sam2:
	@mkdir -p $(SAM2_CKPT_DIR)
	@if [ ! -f "$(SAM2_TINY_CKPT)" ]; then \
		echo "[download] Downloading SAM2 tiny checkpoint..."; \
		curl -L -o $(SAM2_TINY_CKPT) $(SAM2_TINY_URL); \
	else \
		echo "[download] SAM2 checkpoint exists: $(SAM2_TINY_CKPT)"; \
	fi

.PHONY: download-diffusers
download-diffusers:
	@echo "[download] Downloading Diffusers inpaint model via HF mirror..."
	@mkdir -p models/diffusers/stable-diffusion-inpainting
	@HF_ENDPOINT=$(HF_ENDPOINT) \
	HF_HOME=$(HF_HOME) \
	HF_HUB_CACHE=$(HF_HUB_CACHE) \
	HF_XET_HIGH_PERFORMANCE=$(HF_XET_HIGH_PERFORMANCE) \
	hf download runwayml/stable-diffusion-inpainting \
	  --local-dir models/diffusers/stable-diffusion-inpainting \
	  --include "*.json" "*.txt" "*.safetensors" "*.bin" \
	  --local-dir-use-symlinks False || true
	@echo "[download] Diffusers model download step finished."

.PHONY: api
api:
	@PYTHONPATH=src \
	uvicorn sam2_lab.api.server:app \
	  --host $(API_HOST) \
	  --port $(API_PORT) \
	  --reload

.PHONY: ui
ui:
	@PYTHONPATH=src \
	$(PYTHON) -m sam2_lab.app \
	  --host $(API_HOST) \
	  --port $(GRADIO_PORT)

.PHONY: run-all
run-all:
	@mkdir -p outputs/logs outputs/pids
	@echo "[run-all] Starting API on $(API_HOST):$(API_PORT)"
	@PYTHONPATH=src nohup uvicorn sam2_lab.api.server:app \
	  --host $(API_HOST) \
	  --port $(API_PORT) \
	  > outputs/logs/api.log 2>&1 & echo $$! > outputs/pids/api.pid
	@sleep 2
	@echo "[run-all] Starting UI on $(API_HOST):$(GRADIO_PORT)"
	@PYTHONPATH=src nohup $(PYTHON) -m sam2_lab.app \
	  --host $(API_HOST) \
	  --port $(GRADIO_PORT) \
	  > outputs/logs/ui.log 2>&1 & echo $$! > outputs/pids/ui.pid
	@echo "[run-all] Services started."
	@echo "[run-all] API: http://$(API_HOST):$(API_PORT)"
	@echo "[run-all] UI : http://$(API_HOST):$(GRADIO_PORT)"
	@echo "[run-all] Logs: tail -f outputs/logs/api.log outputs/logs/ui.log"
	@echo "[run-all] Stop: make stop"

.PHONY: stop
stop:
	@echo "[stop] Stopping background services..."
	@if [ -f outputs/pids/api.pid ]; then kill $$(cat outputs/pids/api.pid) 2>/dev/null || true; rm -f outputs/pids/api.pid; fi
	@if [ -f outputs/pids/ui.pid ]; then kill $$(cat outputs/pids/ui.pid) 2>/dev/null || true; rm -f outputs/pids/ui.pid; fi
	@echo "[stop] Done."

.PHONY: segment-point
segment-point:
	@PYTHONPATH=src $(PYTHON) scripts/02_segment_point.py \
	  --image $(IMAGE) \
	  --x $(X) \
	  --y $(Y) \
	  --label $(LABEL)

.PHONY: segment-box
segment-box:
	@PYTHONPATH=src $(PYTHON) scripts/03_segment_box.py \
	  --image $(IMAGE) \
	  --x1 $(X1) \
	  --y1 $(Y1) \
	  --x2 $(X2) \
	  --y2 $(Y2)

.PHONY: segment-auto
segment-auto:
	@PYTHONPATH=src $(PYTHON) scripts/04_segment_auto.py \
	  --image $(IMAGE)

.PHONY: quality
quality:
	@PYTHONPATH=src $(PYTHON) scripts/05_mask_quality_report.py \
	  --mask $(MASK)

.PHONY: inpaint
inpaint:
	@PYTHONPATH=src $(PYTHON) scripts/06_sam2_inpaint.py \
	  --image $(IMAGE) \
	  --mask $(MASK) \
	  --prompt "$(PROMPT)"

.PHONY: video-track
video-track:
	@PYTHONPATH=src $(PYTHON) scripts/07_video_track.py \
	  --video data/videos/sample_video.mp4 \
	  --x $(X) \
	  --y $(Y)

.PHONY: smoke
smoke:
	@PYTHONPATH=src $(PYTHON) scripts/99_smoke_test.py

.PHONY: test
test:
	@pytest -q tests

.PHONY: lint
lint:
	@ruff check src scripts tests

.PHONY: format
format:
	@ruff format src scripts tests

.PHONY: clean
clean:
	@echo "[clean] Removing outputs and caches..."
	@rm -rf outputs/masks/* outputs/overlays/* outputs/inpaint/* outputs/video/* outputs/reports/* outputs/manifests/*
	@rm -rf .pytest_cache .ruff_cache
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo "[clean] Done."

.PHONY: clean-models
clean-models:
	@echo "[clean-models] Removing local model files..."
	@rm -rf models/sam2/checkpoints/*
	@rm -rf models/diffusers/*
	@echo "[clean-models] Done."
```

------

## 7. `requirements.txt`

```
torch
torchvision
torchaudio

numpy
opencv-python
pillow
matplotlib
scipy

pydantic
pydantic-settings
pyyaml

fastapi
uvicorn
python-multipart
gradio

huggingface_hub
hf_xet

diffusers
transformers
accelerate
safetensors

pytest
pytest-cov
ruff
mypy
```

------

## 8. `pyproject.toml`

```
[project]
name = "sam2-vision-segmentation-lab"
version = "0.1.0"
description = "SAM 2 pixel-level segmentation lab with mask post-processing and Diffusers inpaint integration."
requires-python = ">=3.11"
authors = [
  { name = "Chenxi" }
]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]
ignore = ["E501"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

------

## 9. 三天开发节奏

### Day 54：SAM 2 Image Predictor 主链路

目标：

```
Point Prompt
Box Prompt
Auto Mask
Overlay 可视化
Manifest 记录
```

任务：

```
make setup
make check-env
make download-models
make segment-point IMAGE=data/images/sample_01.jpg X=400 Y=300
make segment-box IMAGE=data/images/sample_01.jpg X1=100 Y1=80 X2=700 Y2=600
make segment-auto IMAGE=data/images/sample_01.jpg
```

验收物：

```
outputs/masks/*.png
outputs/overlays/*.png
outputs/manifests/segmentation_manifest.jsonl
notebooks/sam2_segmentation_demo.ipynb
```

------

### Day 55：Mask 后处理与质量检测

目标：

```
二值化
形态学开闭运算
连通域过滤
面积统计
孔洞检测
边缘复杂度评估
```

任务：

```
make quality MASK=outputs/masks/sample_01_point_mask.png
pytest -q tests/test_mask_postprocess.py tests/test_quality_report.py
```

验收物：

```
outputs/reports/sample_01_quality.json
docs/mask_quality_metrics.md
至少 3 张不同图片的 mask 质量报告
```

------

### Day 56：SAM 2 + Diffusers Inpaint + Video Tracking

目标：

```
SAM 2 分割目标
Mask 后处理
Diffusers Inpaint 局部重绘
视频帧目标追踪
API / UI 演示
```

任务：

```
make inpaint \
  IMAGE=data/images/sample_01.jpg \
  MASK=outputs/masks/sample_01_point_mask.png \
  PROMPT="a clean futuristic product design background"

make video-track

make run-all
curl http://127.0.0.1:8004/health
```

验收物：

```
outputs/inpaint/*.png
outputs/video/*.mp4
outputs/manifests/inpaint_manifest.jsonl
outputs/manifests/video_tracking_manifest.jsonl
README.md 演示图
```

------

## 10. 常见坑点与硬件降维打击方案

### 10.1 坑点一：SAM 2.1 checkpoint 与旧代码不兼容

现象：

```
RuntimeError: Error(s) in loading state_dict for SAM2Base
```

原因：SAM 2.1 checkpoint 需要最新仓库代码，旧版 `SAM-2` 包可能缺少新模块。官方安装 FAQ 明确建议卸载旧包、拉取最新代码、重新安装。

解决：

```
pip uninstall -y SAM-2 sam2 || true
rm -rf external/sam2
git clone https://github.com/facebookresearch/sam2.git external/sam2
cd external/sam2
SAM2_BUILD_CUDA=0 pip install -e ".[notebooks]"
```

------

### 10.2 坑点二：macOS 上误编译 CUDA 扩展

现象：

```
CUDA_HOME environment variable is not set
Failed to build the SAM 2 CUDA extension
```

解决：

```
cd external/sam2
SAM2_BUILD_CUDA=0 pip install -e ".[notebooks]"
```

解释：MacBook Air M5 没有 CUDA，不要试图解决 `CUDA_HOME`，直接跳过 CUDA extension。

------

### 10.3 坑点三：MPS 上 float16 / bfloat16 报错或结果异常

现象：

```
TypeError: BFloat16 is not supported on MPS
RuntimeError: MPS backend out of memory
```

解决策略：

```
device = "mps"
torch_dtype = torch.float32
pipe = pipe.to(device)
pipe.enable_attention_slicing()
```

在 32GB 统一内存设备上，Diffusers Inpaint 默认 `float32 + attention_slicing` 更稳；不要照 CUDA 教程无脑使用 `float16`。

------

### 10.4 坑点四：全图自动分割生成太多小 mask

现象：

```
detected_masks=300+
outputs/masks 里碎片很多
```

解决：

```
auto_mask:
  pred_iou_thresh: 0.88
  stability_score_thresh: 0.92
  min_mask_region_area: 500
```

同时在后处理加连通域过滤：

```
postprocess_mask(mask, min_area=500)
```

------

### 10.5 坑点五：Point Prompt 坐标写反

错误写法：

```
input_point = np.array([[row, col]])
```

正确写法：

```
input_point = np.array([[x, y]])
```

SAM 2 image predictor 使用图像坐标系：

```
x = 横向坐标，向右增加
y = 纵向坐标，向下增加
```

------

### 10.6 坑点六：端口冲突

现象：

```
[Errno 48] Address already in use
```

检查：

```
lsof -i :8004
lsof -i :7864
```

终止：

```
kill -9 <PID>
```

或者改端口：

```
make api API_PORT=8014
make ui GRADIO_PORT=7874
```

------

### 10.7 坑点七：国内网络拉模型失败

解决：

```
export HF_ENDPOINT=https://hf-mirror.com
export HF_HOME="$PWD/.cache/huggingface"
export HF_HUB_CACHE="$PWD/.cache/huggingface/hub"
export HF_XET_HIGH_PERFORMANCE=1
```

Diffusers 模型使用：

```
hf download runwayml/stable-diffusion-inpainting \
  --local-dir models/diffusers/stable-diffusion-inpainting \
  --include "*.json" "*.txt" "*.safetensors" "*.bin" \
  --local-dir-use-symlinks False
```

SAM 2 checkpoint 使用官方直链兜底：

```
curl -L \
  -o models/sam2/checkpoints/sam2.1_hiera_tiny.pt \
  https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_tiny.pt
```

------

## 11. 产出物 Checklist

```
[ ] README.md（项目门面 + Quick Start + 架构图）
[ ] notebooks/sam2_segmentation_demo.ipynb（Point/Box/后处理完整演示）
[ ] scripts/00_check_env.py（14 项环境自检）
[ ] scripts/01_download_sam2.py
[ ] scripts/02_segment_point.py
[ ] scripts/03_segment_box.py
[ ] scripts/04_segment_auto.py
[ ] scripts/05_mask_quality_report.py（独立 CLI 工具）
[ ] scripts/06_sam2_inpaint.py
[ ] scripts/07_video_track.py（视频追踪）
[ ] scripts/99_smoke_test.py（端到端冒烟）
[ ] src/sam2_lab/sam/loader.py（统一模型加载器）
[ ] src/sam2_lab/sam/image_predictor.py（ImagePredictor 封装类）
[ ] src/sam2_lab/sam/auto_mask.py（全自动分割封装）
[ ] src/sam2_lab/sam/video_predictor.py（VideoTracker 封装类）
[ ] src/sam2_lab/mask/postprocess.py
[ ] src/sam2_lab/mask/quality.py
[ ] src/sam2_lab/mask/geometry.py（质心/bbox/紧凑度）
[ ] src/sam2_lab/mask/visualize.py（轮廓/多色/overlay）
[ ] src/sam2_lab/inpaint/pipeline.py（InpaintPipeline 封装类）
[ ] src/sam2_lab/inpaint/runner.py（分割+修复全流程编排）
[ ] src/sam2_lab/api/server.py（lifespan 模式 FastAPI）
[ ] src/sam2_lab/api/schemas.py（Pydantic 请求/响应模型）
[ ] src/sam2_lab/api/routes.py（health + segment/point + segment/box）
[ ] src/sam2_lab/app.py（Gradio 三 Tab Web UI）
[ ] src/sam2_lab/config.py（YAML 配置加载器）
[ ] src/sam2_lab/logging_utils.py
[ ] src/sam2_lab/utils/image_io.py
[ ] src/sam2_lab/utils/manifest.py
[ ] src/sam2_lab/utils/timer.py
[ ] configs/sam2.yaml, inpaint.yaml, app.yaml, logging.yaml
[ ] outputs/masks 至少 3 张 mask
[ ] outputs/overlays 至少 3 张 overlay
[ ] outputs/reports 至少 3 份 mask 质量报告
[ ] outputs/inpaint 至少 1 张局部重绘结果
[ ] outputs/video 至少 1 组视频追踪结果
[ ] outputs/manifests/segmentation_manifest.jsonl
[ ] tests 全部通过（6 个测试）
[ ] ruff lint 全部通过
[ ] docs/architecture.md, failure_cases.md, interview_notes.md, mask_quality_metrics.md, model_cards.md
```

------

## 12. GitHub README 展示建议

README 第一屏建议写成：

```
# SAM 2 Vision Segmentation Lab

A production-style SAM 2 segmentation engineering lab on Apple Silicon.

Features:
- Point Prompt segmentation
- Box Prompt segmentation
- Automatic mask generation
- Mask post-processing
- Mask quality report
- SAM 2 + Diffusers Inpaint
- Video object tracking
- FastAPI service
- Gradio debug UI
- Reproducible manifest logs
```

建议展示 4 张图：

```
1. 原图
2. Point Prompt overlay
3. Auto Mask top-k overlay
4. Inpaint result
```

------

## 13. 面试深度解析

### Q1：SAM 2 和 SAM 1 在工程数据流上最大的区别是什么？

核心答题思路：

```
SAM 1 主要面向静态图像 promptable segmentation。
SAM 2 把图像和视频统一到一个框架中。
图像可以被视为单帧视频，视频则引入 streaming memory。
```

深度展开：

```
1. 图像分割：
   image encoder 提取视觉特征；
   prompt encoder 编码 point / box / mask；
   mask decoder 输出候选 mask 和 score。

2. 视频分割：
   除了当前帧特征，还需要维护历史 memory；
   用户在某一帧给 prompt；
   模型将目标信息传播到后续帧；
   遮挡、目标消失、再次出现时依赖 memory 做时序一致性。

3. Infra 视角：
   图像分割是 stateless 或 weak-state；
   视频分割是 stateful session；
   API 设计必须保存 session_id、frame_index、object_id、memory state。
```

面试加分点：

```
SAM 2 的视频能力不是简单逐帧跑 SAM，而是把历史帧目标信息写入 memory，再在后续帧中做目标传播。工程上要特别关注显存/统一内存占用、session 生命周期、长视频分段处理。
```

------

### Q2：为什么 Mask 后处理不能只看 IoU score？

核心答题思路：

```
模型 score 只代表模型对当前 mask 的置信度，不等于工程可用性。
真实业务中 mask 是否可用，还取决于几何结构、连通性、孔洞、边缘质量、面积占比。
```

深度展开：

```
1. 面积：
   面积过小可能是噪点；
   面积过大可能吞掉背景。

2. 连通域：
   一个物体通常应该是少量连通域；
   大量碎片说明分割不稳定。

3. 孔洞：
   孔洞可能来自遮挡，也可能是 mask 破损；
   inpaint 时孔洞会导致重绘区域不连续。

4. 边缘：
   边缘点数过多说明轮廓锯齿严重；
   后续用于抠图、重绘、视觉合成时会出现边缘脏线。

5. 后处理：
   形态学 open 去噪；
   close 填孔；
   connected components 过滤小区域；
   contour smoothing 优化边缘。
```

面试加分点：

```
在生成式编辑链路中，mask 是 Diffusers Inpaint 的控制边界。mask 质量比 prompt 更底层，mask 错了，后续再好的 inpaint prompt 也救不回来。
```

------

### Q3：在 Apple Silicon 32GB 统一内存上部署 SAM 2 + Diffusers，如何做资源调度？

核心答题思路：

```
Apple Silicon 是统一内存架构，CPU 和 GPU 共享内存池。
这意味着“显存不够”和“内存不够”不是两个完全独立的问题。
SAM 2 和 Diffusers 同时常驻时，要控制模型尺寸、dtype、分辨率和 pipeline 生命周期。
```

深度展开：

```
1. SAM 2 模型选择：
   默认 tiny；
   small 可选；
   base_plus 谨慎；
   large 不作为默认。

2. 图片尺寸：
   SAM 2 输入最长边控制在 1024；
   auto mask 比 point / box 更耗资源；
   视频追踪要限制帧率和分辨率。

3. Diffusers：
   MPS 默认 float32 更稳；
   启用 attention slicing；
   Inpaint 先用 512x512；
   不要和 SAM 2 large 同时常驻。

4. Pipeline 生命周期：
   API 服务中可 lazy load；
   做完 inpaint 后释放 pipeline；
   必要时调用 gc.collect() 与 torch.mps.empty_cache()。

5. 服务拆分：
   segmentation API 和 inpaint worker 可以拆开；
   简单项目用单进程；
   开源展示用 Makefile 启动 API + UI 即可。
```

面试加分点：

```
CUDA 机器的优化重点是显存；Apple Silicon 的优化重点是统一内存压力、MPS 算子兼容性、dtype 稳定性和模型常驻策略。
```

------

## 14. 最终验收命令

完整验收：

```
conda activate cxllm
cd 04_sam2-vision-segmentation-lab

make setup
make check-env            # 14 项环境自检
make download-models

# 图像分割
make segment-point IMAGE=data/images/sample_01.jpg X=400 Y=300
make segment-box IMAGE=data/images/sample_01.jpg X1=100 Y1=80 X2=700 Y2=600
make segment-auto IMAGE=data/images/sample_01.jpg

# Mask 质量
make quality MASK=outputs/masks/sample_01_point_mask.png

# Inpaint 修复
make inpaint \
  IMAGE=data/images/sample_01.jpg \
  MASK=outputs/masks/sample_01_point_mask.png \
  PROMPT="a clean futuristic product design background"

# 视频追踪
make video-track X=300 Y=250

# 冒烟测试
make smoke

# 单元测试
make test

# 代码质量
make lint

# API 服务
make api &
curl http://127.0.0.1:8004/health

# Gradio UI
make ui &

# 一键启动全栈
make run-all
```

最终项目应该具备：

```
可运行
可复现
可测试
可解释
可展示
可写进简历
可提交 GitHub
```

简历表述：

```
Implemented a production-style SAM 2 visual segmentation lab on Apple Silicon, covering po
```