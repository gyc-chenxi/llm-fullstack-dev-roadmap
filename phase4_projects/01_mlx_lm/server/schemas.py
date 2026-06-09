"""
Pydantic 请求/响应模型
---------------------
与数据库模型分离，仅用于 API 的输入输出序列化。
"""

from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_serializer


# ---------------------------------------------------------------------------
# 聊天相关
# ---------------------------------------------------------------------------

class ChatMessage(BaseModel):
    """单条聊天消息（请求/响应共用）"""
    role: Literal["system", "user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    """POST /v1/chat/completions 请求体"""
    messages: list[ChatMessage]
    max_tokens: int = Field(default=512, ge=1, le=4096)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    # 会话 ID（持久化时使用，可选：新建会话时由后端生成，后续请求传入）
    session_id: Optional[str] = None
    # 系统提示词（可选，覆盖会话级别的 system_prompt）
    system_prompt: Optional[str] = None


# ---------------------------------------------------------------------------
# 会话 CRUD 相关
# ---------------------------------------------------------------------------

class SessionCreate(BaseModel):
    """创建新会话的请求体"""
    title: Optional[str] = None
    system_prompt: Optional[str] = None


class SessionResponse(BaseModel):
    """会话列表/详情响应"""
    id: str
    title: str
    system_prompt: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    # 消息数量（列表接口中返回，详情接口中可能不返回）
    message_count: Optional[int] = None

    # 确保 datetime 序列化时带 UTC 时区标识（SQLite 会丢失 tzinfo）
    @field_serializer("created_at", "updated_at")
    def _serialize_dt(self, dt: datetime) -> str:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()


class MessageResponse(BaseModel):
    """消息列表响应"""
    id: int
    session_id: str
    role: str
    content: str
    created_at: datetime

    @field_serializer("created_at")
    def _serialize_dt(self, dt: datetime) -> str:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
