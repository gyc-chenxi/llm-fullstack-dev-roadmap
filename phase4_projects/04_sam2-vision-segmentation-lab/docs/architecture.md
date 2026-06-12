# 🏗️ 架构设计文档

## 1. 设计哲学

本项目遵循 **"脚本探索 → 模块抽离 → 服务封装"** 的三步工程化方法论：

- **scripts/**: 可独立运行的面向过程脚本，用于快速验证想法
- **src/sam2_lab/**: 可复用的 Python 包，封装核心抽象
- **API/UI**: FastAPI + Gradio 将模型能力暴露为 Web 服务

## 2. 分层架构

```
┌──────────────────────────────────────────────┐
│              表示层 (Presentation)            │
│  app.py (Gradio UI)  │  api/ (FastAPI)       │
├──────────────────────────────────────────────┤
│              业务逻辑层 (Domain)              │
│  sam/ (SAM2 预测器)  │  inpaint/ (修复管线)  │
│  mask/ (后处理+质量) │                        │
├──────────────────────────────────────────────┤
│              基础设施层 (Infrastructure)       │
│  device.py  │  config.py  │  logging_utils.py │
│  utils/ (IO/Timer/Manifest)                  │
├──────────────────────────────────────────────┤
│              外部依赖 (Dependencies)          │
│  SAM 2 (Meta)  │  Diffusers (HF)             │
│  OpenCV  │  PyTorch/MPS                      │
└──────────────────────────────────────────────┘
```

## 3. 关键设计决策

| 决策 | 理由 |
|------|------|
| Apple Silicon 默认 MPS | 目标硬件为 MacBook Pro M 系列 |
| float32 (非 float16) | MPS 对部分 float16 算子支持不完整 |
| attention_slicing 默认开启 | 降低 MPS 显存压力 |
| SAM2 Tiny 默认 | 32GB 统一内存在 Tiny 下推理安全 |
| 本地缓存模型优先 | 避免 HuggingFace 下载，适应网络环境 |
| lifespan 替代 on_event | FastAPI 现代推荐模式，消除 deprecation |
| lazy model loading (Gradio) | 避免 UI 启动时长时间等待 |

## 4. 数据流

```
                    ┌─────────────┐
                    │  图片/视频   │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  SAM2 模型  │
                    └──────┬──────┘
                           │ masks (List[bool ndarray])
                    ┌──────▼──────┐
                    │ Mask 后处理 │  ← postprocess / quality / geometry
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
        ┌─────▼─────┐ ┌───▼────┐ ┌─────▼─────┐
        │ 保存 mask  │ │Inpaint │ │ JSONL     │
        │ overlay    │ │管线    │ │ Manifest  │
        └───────────┘ └────────┘ └───────────┘
```

## 5. 模块依赖关系

```
app.py ──→ sam/loader, sam/image_predictor, inpaint/pipeline, mask/*
api/server ──→ api/routes ──→ api/schemas
api/routes ──→ sam2 (external)
inpaint/runner ──→ sam/loader, sam/image_predictor, mask/postprocess, inpaint/pipeline
scripts/* ──→ sam2 (external) + sam2_lab (optional)
```

核心原则：**上层可依赖下层，下层不反向依赖上层**。
