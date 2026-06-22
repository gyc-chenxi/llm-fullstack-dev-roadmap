# P5: VLM 多模态理解工程实验室

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

基于 Qwen2.5-VL / LLaVA-OneVision 构建的**本地多模态理解工程服务**，支持 OCR、文档解析、图表问答、图像描述、反向 Prompt 生成，并提供 FastAPI 网关 + CLI + Benchmark 完整工程化能力。

> 目标硬件：MacBook Air M5 / 32GB Unified Memory / Apple Silicon MPS

---

## 架构图

```
Image / Screenshot / Chart / Document
        ↓
 Vision Processor (PIL + qwen-vl-utils)
        ↓
 Visual Tokens
        ↓
 Qwen2.5-VL / Qwen2-VL / LLaVA-OneVision
        ↓
 Structured Answer / OCR Text / Markdown Table / Reverse Prompt
        ↓
 FastAPI Gateway (port 8000) → Engine (port 8001)
```

---

## 核心能力

| 能力 | 说明 |
|------|------|
| **OCR 文字提取** | 中英文 OCR，保持换行、层级和表格结构 |
| **表格解析** | 图片表格 → Markdown 表格，不确定单元格标记 `<uncertain>` |
| **图表问答** | 分析 X/Y 轴、趋势、极值点及业务含义 |
| **图像描述** | 3-5 句中文描述主体、背景、构图、氛围 |
| **反向 Prompt** | 图像 → Stable Diffusion / SDXL / Flux 生成提示词（Positive + Negative + Style tags） |
| **双模型支持** | Qwen2.5-VL-3B（主力） + LLaVA-OneVision-0.5B（架构对照） |
| **工程化服务** | FastAPI Engine + Gateway 双层架构，tmux 一键启动 |
| **Apple Silicon 优化** | MPS 后端，32GB 内存精细化管理 |

---

## 模型矩阵

| 用途 | 模型 | 建议 |
|------|------|------|
| 主力模型 | `Qwen/Qwen2.5-VL-3B-Instruct` | 推荐，能力与内存平衡最佳 |
| 保底模型 | `Qwen/Qwen2-VL-2B-Instruct` | MPS 不稳定 / OOM 时切换 |
| 架构对照 | `llava-hf/llava-onevision-qwen2-0.5b-si-hf` | 理解 LLaVA 架构：Vision Encoder → Projector → LLM |

**32GB 内存估算**（以 Qwen2.5-VL-3B 为例）：模型 fp16 ~6GB + Vision tower ~1-3GB + 图像 token/activation ~2-8GB + KV Cache ~1-4GB + Python/Transformers ~2-5GB + 系统 ~6-10GB ≈ 可稳定运行

---

## 环境要求

| 组件 | 要求 |
|------|------|
| OS | macOS (Apple Silicon) / Linux |
| Python | 3.11+ |
| Conda | Miniconda / Anaconda (env: `cxllm`) |
| RAM | 16GB+ (32GB 推荐) |
| Disk | ~20GB (模型文件) |

---

## 快速开始（5 分钟）

```bash
# 1. 进入项目
cd 05-vlm-understanding-lab

# 2. 安装依赖
make setup

# 3. 下载模型（三选一，推荐全部下载）
make download-qwen25    # Qwen2.5-VL-3B（主力）
make download-qwen2     # Qwen2-VL-2B（保底）
make download-llava     # LLaVA-OneVision-0.5B（对照）
# 或一键全部下载
make download-all

# 4. 一键启动服务
make run-all

# 5. 查看日志
make logs
# 按 Ctrl+b 然后 d 退出 tmux
```

---

## API 示例

### 图文问答

```bash
curl -X POST http://127.0.0.1:8000/v1/vision/chat \
  -F "image=@assets/samples/ocr_demo.png" \
  -F "question=请提取图片中的所有文字" \
  | python -m json.tool --no-ensure-ascii
```

<details>
<summary>返回示例</summary>

```json
{
  "answer": "### 会议纪要\n\n1. 项目进度汇报...",
  "model": "models/Qwen2.5-VL-3B-Instruct",
  "device": "mps"
}
```
</details>

### 图表分析

```bash
curl -X POST http://127.0.0.1:8000/v1/vision/chat \
  -F "image=@assets/samples/chart_demo.png" \
  -F "question=请分析这张图表：说明 X 轴、Y 轴、主要趋势、最大值、最小值和可能的业务含义。"
```

### 反向 Prompt 生成

```bash
curl -X POST http://127.0.0.1:8000/v1/vision/chat \
  -F "image=@assets/samples/scene_demo.jpg" \
  -F "question=请分析这张图片，并输出适合 Stable Diffusion / SDXL / Flux 生成用的提示词。严格按格式输出：Positive、Negative、Style tags。"
```

### 健康检查

```bash
# Gateway
curl http://127.0.0.1:8000/health

# Engine（直连）
curl http://127.0.0.1:8001/health
```

---

## Makefile 命令

| 命令 | 说明 |
|------|------|
| `make setup` | 安装 Python 依赖到 Conda 环境 |
| `make env-check` | 打印 Python / Torch / MPS 环境信息 |
| `make download-qwen25` | 下载 Qwen2.5-VL-3B-Instruct |
| `make download-qwen2` | 下载 Qwen2-VL-2B-Instruct |
| `make download-llava` | 下载 LLaVA-OneVision 0.5B |
| `make download-all` | 下载全部推荐模型 |
| `make run-engine` | 启动 Qwen-VL Engine（port 8001） |
| `make run-gateway` | 启动 FastAPI Gateway（port 8000） |
| `make run-all` | tmux 一键启动 Engine + Gateway |
| `make stop` | 停止 tmux 会话 |
| `make logs` | 进入 tmux 查看日志 |
| `make test` | 运行 pytest |
| `make lint` | 运行 ruff 检查 |
| `make clean` | 清理 tmp/cache/output 文件 |
| `make clean-models` | 删除已下载的模型文件 |

---

## 项目结构

```
05-vlm-understanding-lab/
├── Makefile                       # 一键入口
├── pyproject.toml
├── requirements.txt
├── .env.example
│
├── configs/
│   ├── model.qwen25vl-3b.yaml     # Qwen2.5-VL 模型配置
│   ├── model.qwen2vl-2b.yaml      # Qwen2-VL 备选模型配置
│   ├── model.llava-onevision-0.5b.yaml  # LLaVA 架构对照配置
│   └── prompts.yaml               # OCR / 表格 / 图表 / 描述 / 反向 Prompt 模板
│
├── models/                        # 模型文件（.gitkeep，需手动下载）
├── assets/                        # 示例图片
├── outputs/                       # 输出结果（responses / reverse_prompts / benchmark）
│
├── scripts/
│   ├── serve_qwen_vl.py           # Qwen-VL Engine 入口（port 8001）
│   ├── smoke_llava.py             # LLaVA 冒烟测试
│   ├── bench_curl.sh              # curl 性能基准
│   └── print_env.py               # 环境信息打印
│
├── src/vlm_p5/
│   ├── qwen_engine.py             # Qwen-VL 模型引擎封装
│   ├── gateway.py                 # FastAPI 网关（port 8000）
│   ├── schemas.py                 # Pydantic 请求/响应模型
│   └── device.py                  # MPS / CUDA / CPU 设备检测
│
├── tests/                         # 单元测试
├── tmp/uploads/                   # 上传图片暂存
└── Week5_runbook.md               # 完整操作手册
```

---

## 技术栈

| 层级 | 技术 |
|------|------|
| VLM 模型 | Qwen2.5-VL / Qwen2-VL / LLaVA-OneVision |
| 推理框架 | HuggingFace Transformers + qwen-vl-utils |
| API 框架 | FastAPI + Uvicorn |
| 图像处理 | PIL/Pillow + OpenCV |
| 设备加速 | Apple Silicon MPS (Metal Performance Shaders) |
| 模型下载 | HuggingFace Hub + hf_transfer |
| 配置管理 | YAML |
| 测试 | pytest |
| 代码质量 | ruff |

---

## 常见问题

<details>
<summary><b>端口冲突怎么办？</b></summary>

```bash
lsof -i :8000   # Gateway 端口
lsof -i :8001   # Engine 端口
kill -9 <PID>
```
</details>

<details>
<summary><b>32GB 内存 OOM？</b></summary>

降级顺序：切换更小模型（`make download-qwen2`）→ 降低 `MAX_PIXELS` → 降低 `MAX_NEW_TOKENS` → 关闭其他应用
</details>

<details>
<summary><b>MPS 推理报错或结果异常？</b></summary>

```bash
# 尝试用 CPU 运行
export PYTORCH_ENABLE_MPS_FALLBACK=1
# 或切换保底模型
MODEL_BACKEND=qwen2_vl make run-engine
```
</details>

---

## 项目价值表达（简历用）

> 基于 Qwen2.5-VL / LLaVA-OneVision 构建本地多模态理解工程服务，实现 OCR 文字提取、图表问答、表格解析、图像描述与反向 Prompt 生成五大核心能力；采用 FastAPI Engine + Gateway 双层架构，支持 MPS 加速与模型热切换；在 MacBook Air M5 32GB 上完成从模型下载、推理部署到 API 服务的全流程工程化落地。

---

## 许可证

MIT
