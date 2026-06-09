from typing import Literal, Any
from pydantic import BaseModel, Field, model_validator


Role = Literal["system", "user", "assistant", "tool"]


class ChatMessage(BaseModel):
    role: Role
    content: str


class ChatCompletionRequest(BaseModel):
    """
    OpenAI Chat Completions 的最小兼容子集。
    不追求一次性覆盖全部字段，先保证最常用 serving 链路稳定。
    """

    model: str | None = None
    messages: list[ChatMessage] = Field(min_length=1)

    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    top_p: float = Field(default=0.9, ge=0.0, le=1.0)
    max_tokens: int = Field(default=512, ge=1, le=4096)
    stream: bool = False

    # 允许透传 llama.cpp 支持但本 schema 未显式建模的字段。
    extra_body: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_messages(self):
        # 防呆：最后一条通常应是 user，允许高级用户传 assistant prefill，但给出最小保护。
        if not any(m.role == "user" for m in self.messages):
            raise ValueError("messages 至少需要包含一条 user 消息")
        return self

    def to_upstream_payload(self, default_model: str) -> dict[str, Any]:
        payload = {
            "model": self.model or default_model,
            "messages": [m.model_dump() for m in self.messages],
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens,
            "stream": self.stream,
        }
        payload.update(self.extra_body)
        return payload


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    upstream: str
    detail: str | None = None