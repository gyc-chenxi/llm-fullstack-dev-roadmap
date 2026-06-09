"""请求/响应 Pydantic 数据模型"""

from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional
import uuid


class Message(BaseModel):
    """单条对话消息"""
    role: Literal["system", "user", "assistant", "tool"] = Field(
        ..., description="消息角色"
    )
    content: str = Field(..., min_length=1, max_length=100_000, description="消息内容")
    name: Optional[str] = Field(default=None, description="可选发送者名称")


class ChatRequest(BaseModel):
    """聊天请求 — 兼容 OpenAI /v1/chat/completions 格式"""
    messages: list[Message] = Field(..., min_length=1, max_length=100)
    model: str = Field(default="gpt-4o-mini", description="模型名")
    max_tokens: int = Field(default=1024, ge=1, le=32768)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    stream: bool = Field(default=False)
    stop: Optional[list[str]] = Field(default=None)

    @field_validator("messages")
    @classmethod
    def system_must_be_first(cls, v: list[Message]) -> list[Message]:
        """system 消息只能在最前面"""
        for i, msg in enumerate(v):
            if msg.role == "system" and i > 0:
                raise ValueError("system message must be first")
        return v


class ChatChoice(BaseModel):
    index: int = 0
    message: Message
    finish_reason: str = "stop"


class Usage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatResponse(BaseModel):
    """非流式聊天响应"""
    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4().hex[:12]}")
    object: str = "chat.completion"
    created: int = 0
    model: str = ""
    choices: list[ChatChoice]
    usage: Usage = Usage()


class DeltaContent(BaseModel):
    content: Optional[str] = None
    role: Optional[str] = None


class StreamChoice(BaseModel):
    index: int = 0
    delta: DeltaContent = DeltaContent()
    finish_reason: Optional[str] = None


class StreamChunk(BaseModel):
    """流式 SSE 事件格式"""
    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4().hex[:12]}")
    object: str = "chat.completion.chunk"
    created: int = 0
    model: str = ""
    choices: list[StreamChoice]
