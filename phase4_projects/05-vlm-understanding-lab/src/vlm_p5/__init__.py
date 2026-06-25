"""
P5 VLM Understanding Lab
=========================

双层服务架构：
  Client → Gateway (8000, multipart/form-data)
           │  image: UploadFile → 暂存 tmp/uploads/
           │  question: Form str  → JSON payload
           │
           └── httpx POST → Engine (8001, application/json)
                              │  VisionRequest → QwenVLEngine.ask()
                              │
                              │  Image → Vision Encoder → Vision Tokens
                              │    + Text → LLM → Generated Text
                              │
                              └── VisionResponse ← Gateway ← Client

支持的 VLM 后端：Qwen2.5-VL-3B（主力）、Qwen2-VL-2B（保底）、LLaVA-OneVision-0.5B（对照）
推理设备优先级：MPS (Apple Silicon) > CUDA > CPU
"""
