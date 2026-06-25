"""
API 契约 Schemas
=================

请求/响应数据模型（Pydantic v2），用于 Engine 服务的 /generate 端点和
Gateway 的转发逻辑。

数据流：
  Gateway 构造 VisionRequest JSON → POST Engine /generate → VisionResponse JSON
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class VisionRequest(BaseModel):
    """Engine 推理请求。

    image_path: 本地图片路径（由 Gateway 保存上传文件后生成）
    question: 用户自然语言问题
    system_prompt: 可选系统提示词，用于约束模型输出风格
    """
    image_path: str = Field(..., description="Local image path")
    question: str = Field(..., description="User question")
    system_prompt: str | None = Field(None, description="Optional system prompt")


class VisionResponse(BaseModel):
    """Engine 推理响应。

    answer: 模型生成的文本回答（已 strip() 清理）
    model: 当前加载的模型路径（便于区分 Qwen/LLaVA 后端）
    device: 推理设备标识（mps/cuda/cpu）
    """
    answer: str
    model: str
    device: str
