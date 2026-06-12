<p align="center">
  <h1 align="center">🔬 SAM 2 Vision Segmentation Lab</h1>
  <p align="center">
    <strong>基于 Meta SAM 2 的图像/视频分割工程实验平台</strong>
  </p>
  <p align="center">
    <img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python 3.11+">
    <img src="https://img.shields.io/badge/PyTorch-2.x-ee4c2c.svg" alt="PyTorch 2.x">
    <img src="https://img.shields.io/badge/SAM-2.1-green.svg" alt="SAM 2.1">
    <img src="https://img.shields.io/badge/macOS-Apple%20Silicon-silver.svg" alt="Apple Silicon">
    <img src="https://img.shields.io/badge/license-MIT-yellow.svg" alt="License MIT">
  </p>
</p>

---

## 📖 项目简介

**SAM 2 Vision Segmentation Lab** 是一个"从论文到产品"的计算机视觉工程实验项目，聚焦于 Meta AI 发布的 [SAM 2 (Segment Anything Model 2)](https://github.com/facebookresearch/sam2)——目前最强大的通用图像/视频分割基础模型。

项目的核心目标是：**将学术论文中的视觉大模型能力，转化为可复用的 Python 工程包和 Web 服务**。

### 核心能力

| 能力 | 描述 | 状态 |
|------|------|:----:|
| 🎯 **Point 分割** | 用户点击图中目标，AI 精准分割 | ✅ |
| 📦 **Box 分割** | 用户框选区域，AI 分割框内目标 | ✅ |
| 🤖 **全自动分割** | AI 自动发现图中所有物体并分割 | ✅ |
| 🎬 **视频追踪** | 用户在首帧点击目标，AI 追踪目标在所有帧的 mask | ✅ |
| 🎨 **图像修复 (Inpaint)** | SAM2 抠图 → Stable Diffusion 修复背景 | ✅ |
| 📊 **Mask 质量评估** | 连通域/孔洞/边缘复杂度等质量指标 | ✅ |
| 🌐 **Web API** | FastAPI 提供 RESTful 分割接口 | ✅ |
| 🖥️ **Gradio UI** | 拖拽式 Web 交互界面 | 🚧 阶段二 |

---

## 🏗️ 架构总览

```
04_sam2-vision-segmentation-lab/
├── src/sam2_lab/           ← Python 工程包（可 pip install）
│   ├── device.py           │   MPS/CUDA/CPU 自动检测
│   ├── sam/                │   SAM2 预测器封装
│   ├── mask/               │   Mask 后处理 + 质量评估 + 可视化
│   ├── inpaint/            │   SAM2 → Diffusers inpaint 管线
│   ├── api/                │   FastAPI 服务（routes + schemas + server）
│   ├── app.py              │   Gradio Web UI 入口
│   └── utils/              │   图像 I/O、计时、清单记录
│
├── scripts/                ← 独立可执行脚本（可直接 python 运行）
│   ├── 01_download_sam2.py │   下载 SAM2 权重
│   ├── 02_segment_point.py │   Point 分割
│   ├── 03_segment_box.py   │   Box 分割
│   ├── 04_segment_auto.py  │   全自动分割
│   ├── 05_mask_quality_report.py │ 质量报告 CLI
│   ├── 06_sam2_inpaint.py  │   SAM2 + Diffusers 修复
│   ├── 07_video_track.py   │   视频追踪
│   └── 99_smoke_test.py    │   冒烟测试
│
├── configs/                ← YAML 配置文件
├── tests/                  ← pytest 单元测试
├── notebooks/              ← Jupyter 交互笔记
├── docs/                   ← 设计文档 & 面试笔记
├── data/                   ← 测试图片 & 视频
├── models/                 ← 下载的模型权重（不纳入版本控制）
├── outputs/                ← 所有生成产物
├── Makefile                ← 一键式命令入口
└── Week04_runbook.md       ← 详细操作手册
```

### 数据流

```
图片/视频 ──→ [SAM2 分割] ──→ [Mask 后处理] ──→ [质量评估]
                                          │
                                          ├──→ 直接输出 mask/overlay
                                          └──→ [Diffusers Inpaint] ──→ 修复图

                    ──→ [JSONL Manifest] 记录所有处理记录
                    ──→ [FastAPI] 对外提供 API 服务
```

---

## 🚀 快速开始

### 前置要求

- **Python >= 3.11**
- **macOS Apple Silicon（M1/M2/M3/M4）** 或 NVIDIA GPU（CUDA）
- 约 **10 GB** 磁盘空间（含模型权重）

### 一键安装

```bash
# 1. 克隆项目并进入
cd 04_sam2-vision-segmentation-lab

# 2. 安装依赖 + 克隆 SAM2 仓库 + 下载模型
make setup
make download-models

# 3. 环境自检
make check-env
```

### 快速体验

```bash
# Point 分割 — 点击图中某物
make segment-point IMAGE=data/images/sample_01.jpg X=400 Y=300

# Box 分割 — 框选区域
make segment-box X1=100 Y1=80 X2=700 Y2=600

# 全自动分割 — AI 发现所有物体
make segment-auto

# 图像修复 — 抠走物体 + 补全背景
make segment-point                         # 先生成 mask
make inpaint PROMPT="a clean background"   # 再用 mask 做 inpaint

# 视频追踪 — 追随目标跨帧移动（需要先有测试视频）
make video-track X=300 Y=250

# 启动 API
make api                # http://127.0.0.1:8004

# 启动 UI（阶段二完成后）
make ui                 # http://127.0.0.1:7864
```

### 验证一切正常

```bash
make check-env          # 环境检查
make test               # 运行 5 个单元测试
make smoke              # 端到端冒烟测试
make lint               # 代码风格检查
```

---

## 🧪 测试

项目包含 **5 个 pytest 单元测试** + **1 个冒烟测试**：

| 测试文件 | 覆盖内容 |
|----------|----------|
| `test_device.py` | 设备检测 (MPS/CUDA/CPU) |
| `test_mask_postprocess.py` | Mask 去噪/填孔/连通域过滤 |
| `test_quality_report.py` | Mask 质量报告字段完整性 |
| `test_manifest.py` | JSONL 清单追加记录 |
| `test_api_contract.py` | FastAPI `/health` 端点契约 |
| `scripts/99_smoke_test.py` | 端到端冒烟（导入→分割→API） |

```bash
# 运行全部测试
make test

# 带覆盖率
pytest -q tests --cov=src/sam2_lab
```

---

## ⚙️ 配置

所有可调参数集中在 `configs/` 目录：

| 配置文件 | 用途 |
|----------|------|
| `sam2.yaml` | SAM2 模型尺寸、prompt 工程参数、后处理阈值 |
| `inpaint.yaml` | Diffusers 模型路径、生成参数（步数/引导强度） |
| `app.yaml` | API 地址/端口、Gradio 端口 |

---

## 🛠️ 技术栈

| 层 | 技术 |
|----|------|
| **视觉基础模型** | Meta SAM 2.1 (Hiera-Tiny) |
| **扩散模型** | Stable Diffusion Inpainting (runwayml) |
| **深度学习框架** | PyTorch 2.x |
| **图像处理** | OpenCV, NumPy, Pillow |
| **Web API** | FastAPI + Uvicorn |
| **Web UI** | Gradio |
| **配置管理** | PyYAML + Pydantic |
| **测试** | pytest + pytest-cov |
| **代码质量** | Ruff (lint + format) |
| **构建** | GNU Make |

---

## 📚 学习目标

本项目是 **LLM 全栈开发路线图 Phase 4** 的一部分，面向以下学习目标：

1. **视觉基础模型工程化** — 理解 SAM2 的 Promptable Segmentation 范式与推理管线
2. **多模态提示工程** — 掌握 Point/Box/Auto 三种 prompt 方式的适用场景与差异
3. **Mask 后处理管线** — 形态学操作、连通域分析、质量指标
4. **模型管线编排** — SAM2 → Mask → Diffusers 联合推理
5. **视频时序理解** — SAM2 的记忆机制与跨帧 mask 传播
6. **macOS Apple Silicon 适配** — MPS backend、float16/32 取舍、attention slicing
7. **Python 工程化** — 标准包结构、Makefile 构建、pytest 测试、Ruff 规范

---

## 📂 相关文档

- [Week04 Runbook](Week04_runbook.md) — 详细操作手册（包含 Day 54/55/56 三日开发计划）
- [docs/](docs/) — 架构设计、失败案例分析、面试笔记、模型卡片
- [notebooks/](notebooks/) — Jupyter 交互实验笔记

---

## 📄 License

MIT © Chenxi
