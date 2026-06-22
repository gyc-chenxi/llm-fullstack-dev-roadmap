# P5 Runbook: Qwen-VL / LLaVA 多模态理解工程实战

> Week Topic: **P5: Qwen-VL / LLaVA 多模态理解（Day 57-60）**
> Target Hardware: **MacBook Air M5 / 32GB Unified Memory / macOS**
> Target Env: **Conda `cxllm` / Python 3.11 / Apple Silicon MPS**
> Project Goal: 构建一个可开源、可复现、可面试讲解的本地多模态理解工程：支持 OCR、文档解析、图表问答、图像描述、图像反推 Prompt，并理解 LLaVA 架构。

------

## 0. 项目定位与硬件边界

本项目不是“随便跑一个 Notebook”，而是把 VLM 多模态理解能力封装成一个工程化服务：

```text
Image / Screenshot / Chart / Document
        ↓
Vision Processor
        ↓
Visual Tokens
        ↓
Qwen2.5-VL / Qwen2-VL / LLaVA-OneVision
        ↓
Structured Answer / OCR Text / Markdown Table / Reverse Prompt
        ↓
FastAPI Gateway / CLI / Tests / Benchmarks
```

### 推荐模型矩阵

| 用途       | 模型                                        | Mac 32GB 建议 | 说明                                                         |
| ---------- | ------------------------------------------- | ------------- | ------------------------------------------------------------ |
| 主力模型   | `Qwen/Qwen2.5-VL-3B-Instruct`               | 推荐          | 本项目默认主线，能力与内存平衡最好                           |
| 保底模型   | `Qwen/Qwen2-VL-2B-Instruct`                 | 强烈推荐保底  | 网络慢、MPS 不稳定、OOM 时切换                               |
| 架构对照   | `llava-hf/llava-onevision-qwen2-0.5b-si-hf` | 推荐          | 用于理解 LLaVA：Vision Encoder → Projector → LLM             |
| 不推荐默认 | Qwen2.5-VL 7B / LLaVA 7B                    | 谨慎          | 32GB 统一内存能尝试，但服务化稳定性差，不适合作为开源默认路径 |
| 不建议     | 32B / 72B                                   | 不建议        | 超出本机交互式工程训练目标                                   |

### 32GB 统一内存粗略承载估算

以 `Qwen2.5-VL-3B-Instruct` 为例：

```text
模型参数 fp16:      约 6GB
Vision tower/投影层: 约 1-3GB
图像 token / activation: 约 2-8GB，取决于图片分辨率
KV Cache:           约 1-4GB，取决于 max_new_tokens
Python/Transformers: 约 2-5GB
系统与桌面占用:      约 6-10GB
```

结论：

```text
32GB Mac 可以稳定跑 2B/3B VLM；
不要默认跑 7B；
不要一次加载 Qwen-VL 和 LLaVA 7B；
不要输入超高分辨率原图；
不要把 max_new_tokens 拉到 2048 以上。
```

------

## 1. 工程化目录架构

### 1.1 目录树

```text
p5-vlm-understanding-lab/
├── Makefile
├── README.md
├── WeekX_runbook.md
├── pyproject.toml
├── requirements.txt
├── .gitignore
├── .env.example
│
├── configs/
│   ├── model.qwen25vl-3b.yaml
│   ├── model.qwen2vl-2b.yaml
│   ├── model.llava-onevision-0.5b.yaml
│   └── prompts.yaml
│
├── assets/
│   └── samples/
│       ├── ocr_demo.png
│       ├── chart_demo.png
│       ├── table_demo.png
│       └── scene_demo.jpg
│
├── models/
│   └── .gitkeep
│
├── outputs/
│   ├── responses/
│   ├── reverse_prompts/
│   └── benchmark/
│
├── scripts/
│   ├── download_models.sh
│   ├── smoke_qwen_vl.py
│   ├── smoke_llava.py
│   ├── serve_qwen_vl.py
│   ├── bench_curl.sh
│   └── print_env.py
│
├── src/
│   └── vlm_p5/
│       ├── __init__.py
│       ├── device.py
│       ├── config.py
│       ├── qwen_engine.py
│       ├── llava_engine.py
│       ├── prompts.py
│       ├── schemas.py
│       ├── gateway.py
│       └── utils.py
│
├── tests/
│   ├── test_device.py
│   ├── test_prompts.py
│   └── test_api_schema.py
│
└── docs/
    ├── architecture.md
    ├── interview_notes.md
    └── troubleshooting.md
```

### 1.2 目录职责说明

| 路径              | 作用                                                         |
| ----------------- | ------------------------------------------------------------ |
| `configs/`        | 存放模型路径、推理参数、Prompt 模板，避免硬编码。            |
| `assets/samples/` | 存放 OCR、图表、表格、场景图等演示样例。                     |
| `models/`         | 存放 Hugging Face 下载的本地模型权重，不提交 Git。           |
| `outputs/`        | 存放推理结果、反推 Prompt、压测日志和 benchmark 输出。       |
| `scripts/`        | 存放可直接执行的下载、冒烟测试、服务启动、压测脚本。         |
| `src/vlm_p5/`     | 核心 Python 包，包含设备选择、模型引擎、API 网关、数据结构。 |
| `tests/`          | 单元测试，保证配置解析、Prompt 模板、API schema 不被改坏。   |
| `docs/`           | 架构图、面试笔记、踩坑记录，增强 GitHub 项目的展示价值。     |
| `Makefile`        | 统一入口，给小白、面试官和未来的自己提供标准化命令。         |

------

## 2. 初始化工程

### 2.1 创建项目目录

```bash
mkdir -p p5-vlm-understanding-lab
cd p5-vlm-understanding-lab

mkdir -p configs assets/samples models outputs/responses outputs/reverse_prompts outputs/benchmark
mkdir -p scripts src/vlm_p5 tests docs

touch models/.gitkeep
touch src/vlm_p5/__init__.py
touch README.md WeekX_runbook.md .env.example .gitignore
```

### 2.2 `.gitignore`

```gitignore
# Python
__pycache__/
*.py[cod]
.pytest_cache/
.ruff_cache/
.mypy_cache/

# Conda / env
.env
.env.*

# Hugging Face / models
models/*
!models/.gitkeep
.cache/
hf_cache/

# Outputs
outputs/*
!outputs/.gitkeep

# macOS
.DS_Store

# Logs
logs/
*.log

# Temporary files
tmp/
```

------

## 3. 依赖安装与最新工具链配置

### 3.1 激活 Conda 环境

本路线统一使用已有环境 `cxllm`，不使用 `venv`。

```bash
conda activate cxllm

python --version
which python
```

预期：

```text
Python 3.11.x
.../miniconda3/envs/cxllm/bin/python
```

### 3.2 安装基础依赖

```bash
python -m pip install -U pip setuptools wheel

python -m pip install -U \
  torch torchvision torchaudio \
  transformers accelerate safetensors sentencepiece protobuf \
  huggingface_hub hf_transfer \
  qwen-vl-utils \
  pillow opencv-python numpy pyyaml \
  fastapi "uvicorn[standard]" python-multipart httpx \
  pydantic pydantic-settings \
  rich typer tqdm \
  pytest ruff
```

### 3.3 `requirements.txt`

```txt
torch
torchvision
torchaudio

transformers
accelerate
safetensors
sentencepiece
protobuf
huggingface_hub
hf_transfer
qwen-vl-utils

Pillow
opencv-python
numpy
pyyaml

fastapi
uvicorn[standard]
python-multipart
httpx
pydantic
pydantic-settings

rich
typer
tqdm

pytest
ruff
```

### 3.4 `pyproject.toml`

```toml
[project]
name = "p5-vlm-understanding-lab"
version = "0.1.0"
description = "Engineering lab for Qwen-VL / LLaVA multimodal understanding on Apple Silicon."
requires-python = ">=3.11"
authors = [
  { name = "Your Name" }
]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

### 3.5 Apple Silicon / MPS 避坑指南

#### 必须做

```bash
python - <<'PY'
import torch
print("torch:", torch.__version__)
print("mps available:", torch.backends.mps.is_available())
print("mps built:", torch.backends.mps.is_built())
PY
```

预期：

```text
mps available: True
mps built: True
```

#### 建议设置

```bash
export PYTORCH_ENABLE_MPS_FALLBACK=1
export TOKENIZERS_PARALLELISM=false
export HF_HUB_ENABLE_HF_TRANSFER=1
export HF_HOME="$PWD/.cache/huggingface"
```

解释：

| 环境变量                        | 作用                                           |
| ------------------------------- | ---------------------------------------------- |
| `PYTORCH_ENABLE_MPS_FALLBACK=1` | MPS 不支持的算子自动回退 CPU，牺牲速度换稳定。 |
| `TOKENIZERS_PARALLELISM=false`  | 避免 tokenizer 多进程警告和偶发死锁。          |
| `HF_HUB_ENABLE_HF_TRANSFER=1`   | 开启 Hugging Face 下载加速。                   |
| `HF_HOME`                       | 把 HF 缓存限制在项目内，便于清理和复现。       |

#### 不要做

```bash
# 不要在 Mac 上安装 CUDA 版 torch
pip install torch --index-url https://download.pytorch.org/whl/cu121

# 不要默认使用 bitsandbytes
pip install bitsandbytes

# 不要使用 flash-attn
pip install flash-attn
```

原因：

```text
MacBook Air M5 走 Apple Metal / MPS，不走 CUDA。
bitsandbytes 和 flash-attn 主要面向 NVIDIA CUDA 环境。
在 macOS 上强行安装通常不是加速，而是制造依赖冲突。
```

------

## 4. 模型下载

### 4.1 推荐下载顺序

先下载主力 Qwen2.5-VL 3B：

```bash
mkdir -p models

hf download Qwen/Qwen2.5-VL-3B-Instruct \
  --local-dir models/Qwen2.5-VL-3B-Instruct
```

再下载保底 Qwen2-VL 2B：

```bash
hf download Qwen/Qwen2-VL-2B-Instruct \
  --local-dir models/Qwen2-VL-2B-Instruct
```

最后下载 LLaVA 架构对照模型：

```bash
hf download llava-hf/llava-onevision-qwen2-0.5b-si-hf \
  --local-dir models/llava-onevision-qwen2-0.5b-si-hf
```

### 4.2 网络慢时的下载策略

```bash
export HF_ENDPOINT=https://huggingface.co
export HF_HUB_ENABLE_HF_TRANSFER=1
export HF_HOME="$PWD/.cache/huggingface"
```

重新执行：

```bash
hf download Qwen/Qwen2.5-VL-3B-Instruct \
  --local-dir models/Qwen2.5-VL-3B-Instruct \
  --resume-download
```

### 4.3 下载成功检查

```bash
du -sh models/*
find models/Qwen2.5-VL-3B-Instruct -maxdepth 1 -type f | head
```

预期看到：

```text
config.json
generation_config.json
model-xxxxx-of-xxxxx.safetensors
preprocessor_config.json
tokenizer.json
tokenizer_config.json
```

------

## 5. 配置文件

### 5.1 `configs/model.qwen25vl-3b.yaml`

```yaml
model_id: "Qwen/Qwen2.5-VL-3B-Instruct"
local_path: "models/Qwen2.5-VL-3B-Instruct"
backend: "qwen2_5_vl"
device: "auto"
torch_dtype: "float16"
max_new_tokens: 512
max_pixels: 786432
min_pixels: 3136
temperature: 0.0
```

### 5.2 `configs/model.qwen2vl-2b.yaml`

```yaml
model_id: "Qwen/Qwen2-VL-2B-Instruct"
local_path: "models/Qwen2-VL-2B-Instruct"
backend: "qwen2_vl"
device: "auto"
torch_dtype: "float16"
max_new_tokens: 512
max_pixels: 786432
min_pixels: 3136
temperature: 0.0
```

### 5.3 `configs/model.llava-onevision-0.5b.yaml`

```yaml
model_id: "llava-hf/llava-onevision-qwen2-0.5b-si-hf"
local_path: "models/llava-onevision-qwen2-0.5b-si-hf"
backend: "llava_onevision"
device: "auto"
torch_dtype: "float16"
max_new_tokens: 256
temperature: 0.0
```

### 5.4 `configs/prompts.yaml`

```yaml
ocr:
  zh: "请提取图片中的所有文字，尽量保持原始换行、层级和表格结构。"
  en: "Extract all visible text from the image while preserving layout."

table_to_markdown:
  zh: "请解析这张表格图片，并转换为 Markdown 表格。无法确定的单元格用 <uncertain> 标记。"

chart_qa:
  zh: "请分析这张图表：说明 X 轴、Y 轴、主要趋势、最大值、最小值和可能的业务含义。"

image_caption:
  zh: "请用 3-5 句中文描述图片中的主体、背景、颜色、光线、构图和氛围。"

reverse_prompt:
  zh: |
    请分析这张图片，并输出适合 Stable Diffusion / SDXL / Flux 生成用的提示词。
    严格按如下格式输出：
    Positive: <主体、背景、构图、光线、色彩、材质、风格、镜头语言>
    Negative: <低质量、错误结构、文字、水印、畸形等需要避免的元素>
    Style tags: <英文风格标签，用逗号分隔>
```

------

## 6. 核心代码骨架

### 6.1 `src/vlm_p5/device.py`

```python
from __future__ import annotations

import os
import torch


def get_best_device() -> str:
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def get_dtype(device: str) -> torch.dtype:
    if device == "mps":
        return torch.float16
    if device == "cuda":
        return torch.float16
    return torch.float32


def configure_runtime() -> None:
    os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
```

### 6.2 `src/vlm_p5/qwen_engine.py`

```python
from __future__ import annotations

from pathlib import Path
from typing import Optional

import torch
from PIL import Image
from qwen_vl_utils import process_vision_info
from transformers import AutoProcessor, Qwen2VLForConditionalGeneration, Qwen2_5_VLForConditionalGeneration

from vlm_p5.device import configure_runtime, get_best_device, get_dtype


class QwenVLEngine:
    def __init__(
        self,
        model_path: str,
        backend: str = "qwen2_5_vl",
        max_new_tokens: int = 512,
        max_pixels: int = 786432,
        min_pixels: int = 3136,
    ) -> None:
        configure_runtime()

        self.model_path = model_path
        self.backend = backend
        self.device = get_best_device()
        self.dtype = get_dtype(self.device)
        self.max_new_tokens = max_new_tokens

        print(f"[QwenVLEngine] device={self.device}, dtype={self.dtype}")
        print(f"[QwenVLEngine] loading model from {model_path}")

        model_cls = (
            Qwen2_5_VLForConditionalGeneration
            if backend == "qwen2_5_vl"
            else Qwen2VLForConditionalGeneration
        )

        self.model = model_cls.from_pretrained(
            model_path,
            torch_dtype=self.dtype,
            low_cpu_mem_usage=True,
        )

        self.model.to(self.device)
        self.model.eval()

        self.processor = AutoProcessor.from_pretrained(
            model_path,
            min_pixels=min_pixels,
            max_pixels=max_pixels,
        )

        print("[QwenVLEngine] model loaded successfully")

    @torch.inference_mode()
    def ask(self, image_path: str, question: str, system_prompt: Optional[str] = None) -> str:
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        # 提前验证图片，避免 PIL 懒加载导致后面报错难定位
        Image.open(path).convert("RGB")

        content = [
            {"type": "image", "image": str(path)},
            {"type": "text", "text": question},
        ]

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": content})

        text = self.processor.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

        image_inputs, video_inputs = process_vision_info(messages)

        inputs = self.processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt",
        )

        inputs = inputs.to(self.device)

        generated_ids = self.model.generate(
            **inputs,
            max_new_tokens=self.max_new_tokens,
            do_sample=False,
        )

        generated_ids_trimmed = [
            out_ids[len(in_ids):]
            for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]

        output = self.processor.batch_decode(
            generated_ids_trimmed,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        )[0]

        return output.strip()
```

### 6.3 `src/vlm_p5/schemas.py`

```python
from __future__ import annotations

from pydantic import BaseModel, Field


class VisionRequest(BaseModel):
    image_path: str = Field(..., description="Local image path")
    question: str = Field(..., description="User question")
    system_prompt: str | None = Field(None, description="Optional system prompt")


class VisionResponse(BaseModel):
    answer: str
    model: str
    device: str
```

### 6.4 `scripts/serve_qwen_vl.py`

```python
from __future__ import annotations

import os

import uvicorn
from fastapi import FastAPI

from vlm_p5.qwen_engine import QwenVLEngine
from vlm_p5.schemas import VisionRequest, VisionResponse

MODEL_PATH = os.getenv("MODEL_PATH", "models/Qwen2.5-VL-3B-Instruct")
MODEL_BACKEND = os.getenv("MODEL_BACKEND", "qwen2_5_vl")
MAX_NEW_TOKENS = int(os.getenv("MAX_NEW_TOKENS", "512"))
MAX_PIXELS = int(os.getenv("MAX_PIXELS", "786432"))

app = FastAPI(title="P5 Qwen-VL Engine", version="0.1.0")

engine: QwenVLEngine | None = None


@app.on_event("startup")
def startup() -> None:
    global engine
    engine = QwenVLEngine(
        model_path=MODEL_PATH,
        backend=MODEL_BACKEND,
        max_new_tokens=MAX_NEW_TOKENS,
        max_pixels=MAX_PIXELS,
    )


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "model_path": MODEL_PATH,
        "backend": MODEL_BACKEND,
    }


@app.post("/generate", response_model=VisionResponse)
def generate(req: VisionRequest) -> VisionResponse:
    assert engine is not None
    answer = engine.ask(
        image_path=req.image_path,
        question=req.question,
        system_prompt=req.system_prompt,
    )
    return VisionResponse(
        answer=answer,
        model=MODEL_PATH,
        device=engine.device,
    )


if __name__ == "__main__":
    uvicorn.run(
        "scripts.serve_qwen_vl:app",
        host="127.0.0.1",
        port=8001,
        reload=False,
    )
```

### 6.5 `src/vlm_p5/gateway.py`

```python
from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import httpx
import uvicorn
from fastapi import FastAPI, File, Form, UploadFile

app = FastAPI(title="P5 VLM Gateway", version="0.1.0")

TMP_DIR = Path("tmp/uploads")
TMP_DIR.mkdir(parents=True, exist_ok=True)

ENGINE_URL = "http://127.0.0.1:8001/generate"


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "gateway"}


@app.post("/v1/vision/chat")
async def vision_chat(
    image: UploadFile = File(...),
    question: str = Form(...),
) -> dict:
    suffix = Path(image.filename or "image.png").suffix or ".png"
    image_path = TMP_DIR / f"{uuid.uuid4().hex}{suffix}"

    with image_path.open("wb") as f:
        shutil.copyfileobj(image.file, f)

    payload = {
        "image_path": str(image_path),
        "question": question,
    }

    async with httpx.AsyncClient(timeout=300.0) as client:
        resp = await client.post(ENGINE_URL, json=payload)
        resp.raise_for_status()
        return resp.json()


if __name__ == "__main__":
    uvicorn.run(
        "vlm_p5.gateway:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
    )
```

------

## 7. 分终端执行与测试流程

### 7.1 终端 0：环境检查

```bash
cd p5-vlm-understanding-lab
conda activate cxllm

python scripts/print_env.py
```

`scripts/print_env.py`：

```python
import platform
import torch
import transformers

print("python:", platform.python_version())
print("platform:", platform.platform())
print("torch:", torch.__version__)
print("transformers:", transformers.__version__)
print("mps available:", torch.backends.mps.is_available())
print("mps built:", torch.backends.mps.is_built())
```

预期成功日志：

```text
python: 3.11.x
platform: macOS-...
torch: ...
transformers: ...
mps available: True
mps built: True
```

------

### 7.2 终端 1：启动 Qwen-VL 底座服务

```bash
cd p5-vlm-understanding-lab
conda activate cxllm

export PYTHONPATH="$PWD/src:$PWD"
export PYTORCH_ENABLE_MPS_FALLBACK=1
export TOKENIZERS_PARALLELISM=false
export HF_HOME="$PWD/.cache/huggingface"

export MODEL_PATH="models/Qwen2.5-VL-3B-Instruct"
export MODEL_BACKEND="qwen2_5_vl"
export MAX_NEW_TOKENS=512
export MAX_PIXELS=786432

python scripts/serve_qwen_vl.py
```

预期看到：

```text
[QwenVLEngine] device=mps, dtype=torch.float16
[QwenVLEngine] loading model from models/Qwen2.5-VL-3B-Instruct
[QwenVLEngine] model loaded successfully
Uvicorn running on http://127.0.0.1:8001
```

健康检查：

```bash
curl http://127.0.0.1:8001/health
```

预期：

```json
{
  "status": "ok",
  "model_path": "models/Qwen2.5-VL-3B-Instruct",
  "backend": "qwen2_5_vl"
}
```

------

### 7.3 终端 2：启动 API Gateway

```bash
cd p5-vlm-understanding-lab
conda activate cxllm

export PYTHONPATH="$PWD/src:$PWD"
python -m vlm_p5.gateway
```

预期看到：

```text
Uvicorn running on http://127.0.0.1:8000
```

健康检查：

```bash
curl http://127.0.0.1:8000/health
```

预期：

```json
{
  "status": "ok",
  "service": "gateway"
}
```

------

### 7.4 终端 3：Curl 测试 OCR

```bash
curl -X POST "http://127.0.0.1:8000/v1/vision/chat" \
  -F "image=@assets/samples/ocr_demo.png" \
  -F "question=请提取图片中的所有文字，保持原始格式。"
```

预期输出：

```json
{
  "answer": "...图片中的文字...",
  "model": "models/Qwen2.5-VL-3B-Instruct",
  "device": "mps"
}
```

------

### 7.5 测试表格转 Markdown

```bash
curl -X POST "http://127.0.0.1:8000/v1/vision/chat" \
  -F "image=@assets/samples/table_demo.png" \
  -F "question=请把图片中的表格转换成 Markdown 表格，无法确认的单元格用 <uncertain> 标记。"
```

预期输出包含：

```markdown
| 列1 | 列2 | 列3 |
|---|---|---|
| ... | ... | ... |
```

------

### 7.6 测试图表问答

```bash
curl -X POST "http://127.0.0.1:8000/v1/vision/chat" \
  -F "image=@assets/samples/chart_demo.png" \
  -F "question=请分析这个图表：X轴、Y轴、趋势、最大值、最小值分别是什么？"
```

预期输出包含：

```text
X 轴代表...
Y 轴代表...
整体趋势...
最大值...
最小值...
```

------

### 7.7 测试图像反推 Prompt

```bash
curl -X POST "http://127.0.0.1:8000/v1/vision/chat" \
  -F "image=@assets/samples/scene_demo.jpg" \
  -F "question=请分析这张图片，并输出适合 Stable Diffusion 生成用的 Positive、Negative 和 Style tags。"
```

预期输出：

```text
Positive: ...
Negative: ...
Style tags: ...
```

------

## 8. LLaVA 架构对照实验

Qwen-VL 主打中文 OCR、文档理解、图表解析。LLaVA 对本周更重要的价值是理解经典 VLM 架构：

```text
Image
  ↓
Vision Encoder，例如 CLIP / SigLIP
  ↓
Projector，把视觉特征映射到 LLM hidden size
  ↓
LLM，例如 Vicuna / Llama / Mistral / Qwen
  ↓
Text Answer
```

### 8.1 `scripts/smoke_llava.py`

```python
from __future__ import annotations

import torch
from PIL import Image
from transformers import LlavaOnevisionForConditionalGeneration, AutoProcessor

from vlm_p5.device import configure_runtime, get_best_device, get_dtype

configure_runtime()

model_path = "models/llava-onevision-qwen2-0.5b-si-hf"
image_path = "assets/samples/scene_demo.jpg"

device = get_best_device()
dtype = get_dtype(device)

print(f"[LLaVA] device={device}, dtype={dtype}")

model = LlavaOnevisionForConditionalGeneration.from_pretrained(
    model_path,
    torch_dtype=dtype,
    low_cpu_mem_usage=True,
)
model.to(device)
model.eval()

processor = AutoProcessor.from_pretrained(model_path)

conversation = [
    {
        "role": "user",
        "content": [
            {"type": "image"},
            {"type": "text", "text": "Describe this image in detail."},
        ],
    }
]

prompt = processor.apply_chat_template(
    conversation,
    add_generation_prompt=True,
)

image = Image.open(image_path).convert("RGB")

inputs = processor(
    images=image,
    text=prompt,
    return_tensors="pt",
).to(device)

with torch.inference_mode():
    output = model.generate(
        **inputs,
        max_new_tokens=256,
        do_sample=False,
    )

print(processor.decode(output[0], skip_special_tokens=True))
```

运行：

```bash
conda activate cxllm
export PYTHONPATH="$PWD/src:$PWD"
python scripts/smoke_llava.py
```

预期：

```text
[LLaVA] device=mps, dtype=torch.float16
...
The image shows...
```

------

## 9. 终极一键运行：Makefile 集成

### 9.1 Makefile 源码

```makefile
SHELL := /bin/bash

CONDA_ENV := cxllm
PYTHON := conda run -n $(CONDA_ENV) python
PIP := conda run -n $(CONDA_ENV) python -m pip

PROJECT_ROOT := $(shell pwd)
PYTHONPATH_VALUE := $(PROJECT_ROOT)/src:$(PROJECT_ROOT)

QWEN25_MODEL := models/Qwen2.5-VL-3B-Instruct
QWEN2_MODEL := models/Qwen2-VL-2B-Instruct
LLAVA_MODEL := models/llava-onevision-qwen2-0.5b-si-hf

ENGINE_PORT := 8001
GATEWAY_PORT := 8000
TMUX_SESSION := p5-vlm

.PHONY: help setup env-check download-qwen25 download-qwen2 download-llava download-all \
        run-engine run-gateway run-all stop logs test lint clean clean-models clean-cache

help:
	@echo ""
	@echo "P5 VLM Understanding Lab"
	@echo ""
	@echo "Available commands:"
	@echo "  make setup           Install Python dependencies into Conda env: $(CONDA_ENV)"
	@echo "  make env-check       Print Python / Torch / MPS environment"
	@echo "  make download-qwen25 Download Qwen2.5-VL-3B-Instruct"
	@echo "  make download-qwen2  Download Qwen2-VL-2B-Instruct fallback"
	@echo "  make download-llava  Download LLaVA-OneVision 0.5B"
	@echo "  make download-all    Download all recommended models"
	@echo "  make run-engine      Run Qwen-VL engine on port $(ENGINE_PORT)"
	@echo "  make run-gateway     Run FastAPI gateway on port $(GATEWAY_PORT)"
	@echo "  make run-all         Start engine + gateway in tmux"
	@echo "  make stop            Stop tmux session"
	@echo "  make logs            Attach tmux session"
	@echo "  make test            Run pytest"
	@echo "  make lint            Run ruff"
	@echo "  make clean           Clean tmp/cache/output files"
	@echo "  make clean-models    Remove downloaded model files"
	@echo ""

setup:
	$(PIP) install -U pip setuptools wheel
	$(PIP) install -r requirements.txt

env-check:
	PYTHONPATH=$(PYTHONPATH_VALUE) \
	$(PYTHON) scripts/print_env.py

download-qwen25:
	mkdir -p models
	HF_HUB_ENABLE_HF_TRANSFER=1 HF_HOME=$(PROJECT_ROOT)/.cache/huggingface \
	conda run -n $(CONDA_ENV) hf download Qwen/Qwen2.5-VL-3B-Instruct \
		--local-dir $(QWEN25_MODEL)

download-qwen2:
	mkdir -p models
	HF_HUB_ENABLE_HF_TRANSFER=1 HF_HOME=$(PROJECT_ROOT)/.cache/huggingface \
	conda run -n $(CONDA_ENV) hf download Qwen/Qwen2-VL-2B-Instruct \
		--local-dir $(QWEN2_MODEL)

download-llava:
	mkdir -p models
	HF_HUB_ENABLE_HF_TRANSFER=1 HF_HOME=$(PROJECT_ROOT)/.cache/huggingface \
	conda run -n $(CONDA_ENV) hf download llava-hf/llava-onevision-qwen2-0.5b-si-hf \
		--local-dir $(LLAVA_MODEL)

download-all: download-qwen25 download-qwen2 download-llava

run-engine:
	PYTHONPATH=$(PYTHONPATH_VALUE) \
	PYTORCH_ENABLE_MPS_FALLBACK=1 \
	TOKENIZERS_PARALLELISM=false \
	HF_HOME=$(PROJECT_ROOT)/.cache/huggingface \
	MODEL_PATH=$(QWEN25_MODEL) \
	MODEL_BACKEND=qwen2_5_vl \
	MAX_NEW_TOKENS=512 \
	MAX_PIXELS=786432 \
	$(PYTHON) scripts/serve_qwen_vl.py

run-gateway:
	PYTHONPATH=$(PYTHONPATH_VALUE) \
	PYTORCH_ENABLE_MPS_FALLBACK=1 \
	TOKENIZERS_PARALLELISM=false \
	$(PYTHON) -m vlm_p5.gateway

run-all:
	@command -v tmux >/dev/null 2>&1 || { echo "tmux not found. Install with: brew install tmux"; exit 1; }
	@tmux has-session -t $(TMUX_SESSION) 2>/dev/null && { echo "tmux session $(TMUX_SESSION) already exists. Run: make logs"; exit 0; } || true
	@tmux new-session -d -s $(TMUX_SESSION) -n engine
	@tmux send-keys -t $(TMUX_SESSION):engine "cd $(PROJECT_ROOT) && make run-engine" C-m
	@sleep 8
	@tmux new-window -t $(TMUX_SESSION) -n gateway
	@tmux send-keys -t $(TMUX_SESSION):gateway "cd $(PROJECT_ROOT) && make run-gateway" C-m
	@tmux new-window -t $(TMUX_SESSION) -n curl
	@tmux send-keys -t $(TMUX_SESSION):curl "cd $(PROJECT_ROOT) && echo 'Engine: http://127.0.0.1:$(ENGINE_PORT)/health' && echo 'Gateway: http://127.0.0.1:$(GATEWAY_PORT)/health'" C-m
	@echo "Started tmux session: $(TMUX_SESSION)"
	@echo "Attach logs: make logs"
	@echo "Stop services: make stop"

stop:
	@tmux kill-session -t $(TMUX_SESSION) 2>/dev/null || true
	@echo "Stopped tmux session: $(TMUX_SESSION)"

logs:
	tmux attach -t $(TMUX_SESSION)

test:
	PYTHONPATH=$(PYTHONPATH_VALUE) \
	$(PYTHON) -m pytest -q

lint:
	PYTHONPATH=$(PYTHONPATH_VALUE) \
	$(PYTHON) -m ruff check src scripts tests

clean:
	rm -rf tmp
	rm -rf outputs/responses/* outputs/reverse_prompts/* outputs/benchmark/*
	rm -rf .pytest_cache .ruff_cache
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +

clean-cache:
	rm -rf .cache/huggingface

clean-models:
	rm -rf models/*
	touch models/.gitkeep
```

### 9.2 一键运行方式

首次安装：

```bash
make setup
make env-check
make download-qwen25
make run-all
```

查看服务：

```bash
make logs
```

停止服务：

```bash
make stop
```

清理输出：

```bash
make clean
```

清理模型：

```bash
make clean-models
```

------

## 10. 冒烟测试脚本

### 10.1 `scripts/bench_curl.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

IMAGE="${1:-assets/samples/ocr_demo.png}"
QUESTION="${2:-请提取图片中的所有文字，保持原始格式。}"

curl -s -X POST "http://127.0.0.1:8000/v1/vision/chat" \
  -F "image=@${IMAGE}" \
  -F "question=${QUESTION}" | python -m json.tool
```

赋权：

```bash
chmod +x scripts/bench_curl.sh
```

运行：

```bash
./scripts/bench_curl.sh assets/samples/ocr_demo.png "请提取图片中的所有文字。"
./scripts/bench_curl.sh assets/samples/table_demo.png "请转换为 Markdown 表格。"
./scripts/bench_curl.sh assets/samples/chart_demo.png "请分析图表趋势。"
./scripts/bench_curl.sh assets/samples/scene_demo.jpg "请反推 Stable Diffusion 提示词。"
```

------

## 11. Day 57-60 实战安排

### Day 57：Qwen-VL 环境与 OCR

目标：

```text
完成 Conda 环境、模型下载、Qwen2.5-VL-3B 首次推理。
```

任务：

```bash
make setup
make env-check
make download-qwen25
make run-engine
```

验收：

```text
1. MPS 可用。
2. Qwen2.5-VL-3B 成功加载。
3. OCR 图片能输出完整中文文本。
```

------

### Day 58：文档解析与图表问答

目标：

```text
构造 table_demo.png / chart_demo.png，验证结构化输出能力。
```

任务：

```bash
make run-all

./scripts/bench_curl.sh assets/samples/table_demo.png \
  "请把图片中的表格转换成 Markdown 表格，无法确认的单元格用 <uncertain> 标记。"

./scripts/bench_curl.sh assets/samples/chart_demo.png \
  "请分析图表：X轴、Y轴、趋势、最大值、最小值和业务含义。"
```

验收：

```text
1. 表格能输出 Markdown。
2. 图表能识别坐标轴和趋势。
3. 对不确定内容能显式标记，而不是胡编。
```

------

### Day 59：LLaVA 架构对照

目标：

```text
跑通 LLaVA-OneVision 小模型，理解 Vision Encoder → Projector → LLM。
```

任务：

```bash
make download-llava
PYTHONPATH="$PWD/src:$PWD" python scripts/smoke_llava.py
```

验收：

```text
1. LLaVA 小模型能生成图片描述。
2. 能讲清楚 Projector 的作用。
3. 能比较 Qwen-VL 与 LLaVA 的工程差异。
```

------

### Day 60：图像反推 Prompt 与工程封装

目标：

```text
把 VLM 输出转换为 AIGC 生产可用的 Prompt 结构。
```

任务：

```bash
./scripts/bench_curl.sh assets/samples/scene_demo.jpg \
  "请分析图片并输出 Positive、Negative、Style tags，适合 SDXL 或 Flux 使用。"
```

验收：

```text
1. 输出包含 Positive / Negative / Style tags。
2. 主体、构图、光线、色彩、风格都有覆盖。
3. 不把 OCR/水印/错误文字写进 Positive。
4. README 能让别人 clone 后按 Makefile 跑通。
```

------

## 12. 常见坑点与硬件降维打击方案

### 坑 1：MPS 可用，但模型推理中途报 unsupported op

现象：

```text
RuntimeError: The operator ... is not currently implemented for the MPS device
```

解决：

```bash
export PYTORCH_ENABLE_MPS_FALLBACK=1
```

如果仍然报错：

```bash
export MODEL_PATH="models/Qwen2-VL-2B-Instruct"
export MODEL_BACKEND="qwen2_vl"
make run-engine
```

工程解释：

```text
MPS 后端覆盖率不断提升，但部分动态 shape / vision op 可能仍会落到 CPU。
本项目默认允许 fallback，优先保证可跑通。
```

------

### 坑 2：OOM 或系统内存压力过高

现象：

```text
zsh: killed
RuntimeError: MPS backend out of memory
macOS memory pressure red
```

优先级处理：

```bash
# 1. 降低图片 token 数
export MAX_PIXELS=262144

# 2. 降低生成长度
export MAX_NEW_TOKENS=256

# 3. 切换 2B 模型
export MODEL_PATH="models/Qwen2-VL-2B-Instruct"
export MODEL_BACKEND="qwen2_vl"

# 4. 关闭浏览器、IDE、ComfyUI、Docker Desktop 等高内存进程
```

不要做：

```bash
不要同时加载 Qwen2.5-VL-3B 和 LLaVA 7B。
不要上传 4K/8K 原图。
不要把 max_new_tokens 设置到 2048。
```

------

### 坑 3：端口冲突

现象：

```text
[Errno 48] Address already in use
```

排查：

```bash
lsof -i :8000
lsof -i :8001
```

杀进程：

```bash
kill -9 <PID>
```

或者停止 tmux 服务：

```bash
make stop
```

------

### 坑 4：Hugging Face 下载失败 / 代理劫持 / SSL 错误

现象：

```text
Distant resource does not seem to be on huggingface.co
SSLError
Connection reset
```

处理：

```bash
unset HTTP_PROXY
unset HTTPS_PROXY
unset ALL_PROXY

export HF_ENDPOINT=https://huggingface.co
export HF_HUB_ENABLE_HF_TRANSFER=1
export HF_HOME="$PWD/.cache/huggingface"

hf download Qwen/Qwen2.5-VL-3B-Instruct \
  --local-dir models/Qwen2.5-VL-3B-Instruct \
  --resume-download
```

如果你必须走代理：

```bash
export HTTPS_PROXY=http://127.0.0.1:7890
export HTTP_PROXY=http://127.0.0.1:7890
```

验证：

```bash
python - <<'PY'
from huggingface_hub import model_info
print(model_info("Qwen/Qwen2.5-VL-3B-Instruct").modelId)
PY
```

------

### 坑 5：`device_map="auto"` 在 Mac 上不稳定

很多 CUDA 教程会写：

```python
device_map="auto"
```

在 Mac 工程里不建议默认依赖它。更稳妥的方式是：

```python
model = ModelClass.from_pretrained(
    model_path,
    torch_dtype=torch.float16,
    low_cpu_mem_usage=True,
)
model.to("mps")
```

原因：

```text
device_map="auto" 主要适合多 GPU / CUDA / accelerate 分片场景。
Mac 单机 MPS 更适合手动选择 device，减少不可控行为。
```

------

### 坑 6：OCR 结果差，不一定是模型差

常见原因：

```text
1. 输入图片太糊。
2. 字体高度太小。
3. 截图压缩严重。
4. 表格线和文字对比度低。
5. 问题太泛，没有要求保持格式。
```

改进 Prompt：

```text
请提取图片中的所有文字。
要求：
1. 保持原始换行。
2. 表格用 Markdown 输出。
3. 不确定的文字用 <uncertain> 标记。
4. 不要补充图片中不存在的内容。
```

------

## 13. README 建议写法

GitHub 首页建议突出四件事：

```text
1. 本项目能做什么：OCR / 文档解析 / 图表问答 / 图像反推 Prompt。
2. 本项目为什么适合 Mac：默认 Qwen2.5-VL-3B + MPS fallback + Makefile。
3. 如何一键跑：make setup → make download-qwen25 → make run-all。
4. 面试价值：能讲清 VLM 数据流、服务拆分、内存瓶颈、模型降级策略。
```

README 最小命令：

```bash
conda activate cxllm
make setup
make env-check
make download-qwen25
make run-all
make logs
```

Curl 示例：

```bash
curl -X POST "http://127.0.0.1:8000/v1/vision/chat" \
  -F "image=@assets/samples/ocr_demo.png" \
  -F "question=请提取图片中的所有文字。"
```

------

## 14. 产出物 Checklist

```text
[ ] Conda cxllm 环境可复现
[ ] Qwen2.5-VL-3B-Instruct 下载成功
[ ] Qwen2-VL-2B-Instruct 保底模型下载成功
[ ] LLaVA-OneVision 0.5B 架构对照跑通
[ ] FastAPI Engine 服务可用
[ ] Gateway 文件上传接口可用
[ ] OCR Demo 可用
[ ] 表格转 Markdown Demo 可用
[ ] 图表问答 Demo 可用
[ ] 图像描述 Demo 可用
[ ] Reverse Prompt Demo 可用
[ ] Makefile 一键启动可用
[ ] README 可让别人 clone 后复现
[ ] docs/interview_notes.md 完成
```

------

## 15. 面试深度解析

### 题 1：VLM 的图像是如何进入 LLM 的？为什么图片分辨率会影响显存？

核心答题思路：

```text
VLM 并不是让 LLM 直接看像素，而是先通过 Vision Encoder 把图片编码成视觉特征。
这些视觉特征经过 Projector 映射到 LLM 的 hidden size，再作为 visual tokens 拼接进文本 token 序列。
因此，图片越大，视觉 token 越多，prefill 阶段 attention 成本越高，activation 和 KV cache 压力越大。
在 Apple Silicon 上，统一内存虽然让 CPU/GPU 共享内存更方便，但并不意味着无限显存。
当图片 token、生成长度、模型参数同时变大时，MPS 会出现 memory pressure，最终进程被系统杀掉。
工程上要控制 max_pixels、max_new_tokens，并提供 3B → 2B 的降级策略。
```

加分点：

```text
VLM serving 的瓶颈通常不是 decode 阶段，而是 image preprocessing + multimodal prefill。
文本 LLM 主要受上下文长度影响；VLM 额外受图片分辨率、patch 数、视觉 token 合并策略影响。
```

------

### 题 2：Qwen-VL 和 LLaVA 的工程关注点有什么不同？

核心答题思路：

```text
LLaVA 是理解 VLM 架构非常经典的路线：Vision Encoder → Projector → LLM。
它的核心价值是用视觉指令微调把图像特征接入语言模型，让 LLM 具备图文对话能力。

Qwen-VL / Qwen2.5-VL 更偏综合能力和工程可用性，尤其在中文 OCR、文档解析、表格、图表、空间定位、多语言场景上更适合做应用层 Demo。
所以本项目把 Qwen2.5-VL-3B 作为主力模型，把 LLaVA-OneVision 小模型作为架构对照。
```

加分点：

```text
面试时不要只说“哪个模型效果好”，要说“哪个模型适合当前硬件和产品路径”。
MacBook Air M5 32GB 的目标是稳定跑通工程闭环，不是追求榜单极限。
```

------

### 题 3：如果要把本项目升级为生产级 VLM 服务，你会怎么改？

核心答题思路：

```text
第一层：服务拆分。
把模型引擎和 API Gateway 分离。Gateway 负责鉴权、文件上传、限流、请求校验；Engine 负责模型加载和推理。

第二层：资源治理。
限制图片大小、max_new_tokens、并发数。对大图做 resize，对重复图片做 hash cache，对长任务设置 timeout。

第三层：可观测性。
记录每次请求的 image_size、prompt_tokens、generated_tokens、latency、error_type、memory pressure。

第四层：降级策略。
主力模型不可用时降级到 2B；MPS 算子失败时允许 CPU fallback；高负载时拒绝超大图或长输出。

第五层：批处理与队列。
生产中不能让多个请求同时抢占统一内存。Mac 本地服务可以用单 worker + 队列，NVIDIA 服务可以进一步考虑 continuous batching。
```

加分点：

```text
VLM 的生产问题不是“能不能 generate”，而是：
1. 输入文件不可控；
2. 图片 token 成本不可控；
3. 并发下内存峰值不可控；
4. OCR/文档任务容易产生幻觉；
5. 需要结构化输出和不确定性标记。
```

------

## 16. 本周最终交付标准

本周完成后，你应该能在 GitHub 项目中证明三件事：

```text
1. 我会用 Qwen2.5-VL 做真实多模态应用，而不是只跑 Notebook。
2. 我理解 LLaVA 的底层架构，而不是只知道模型名字。
3. 我能基于 Mac Apple Silicon 的真实硬件约束做工程取舍、服务封装、Makefile 自动化和故障降级。
```

最终项目展示命令：

```bash
git clone <your-repo>
cd p5-vlm-understanding-lab
conda activate cxllm
make setup
make download-qwen25
make run-all
make logs
```

最终 Demo 命令：

```bash
./scripts/bench_curl.sh assets/samples/ocr_demo.png "请提取图片中的所有文字。"
./scripts/bench_curl.sh assets/samples/table_demo.png "请转换为 Markdown 表格。"
./scripts/bench_curl.sh assets/samples/chart_demo.png "请分析图表趋势。"
./scripts/bench_curl.sh assets/samples/scene_demo.jpg "请反推 Stable Diffusion 提示词。"
```