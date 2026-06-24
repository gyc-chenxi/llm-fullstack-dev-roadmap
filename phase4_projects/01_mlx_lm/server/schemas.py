"""
Pydantic 请求/响应模型
---------------------
与数据库模型 (models.py) 分离，仅用于 API 的输入输出序列化和校验。

分层设计说明：
  ChatRequest  → routes/chat.py POST 端点消费
  SessionCreate → routes/sessions.py POST 端点消费
  SessionResponse / MessageResponse → 返回给前端的数据格式
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
    """POST /v1/chat/completions 请求体，对标 OpenAI API 格式"""
    messages: list[ChatMessage]                     # 对话历史（含 system/user/assistant）
    max_tokens: int = Field(default=512, ge=1, le=4096)      # 最大生成 token 数，限制 ≤4096 避免超长输出
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)  # 采样温度，0=确定，1=平衡，>1=高随机
    session_id: Optional[str] = None       # 会话 ID（新建时由后端生成并返回，后续请求传入）
    system_prompt: Optional[str] = None    # 可覆盖会话级别 system_prompt 的系统提示词


# ---------------------------------------------------------------------------
# 会话 CRUD 相关
# ---------------------------------------------------------------------------

class SessionCreate(BaseModel):
    """创建新会话的请求体"""
    title: Optional[str] = None           # 可选，不传则后端自动生成
    system_prompt: Optional[str] = None    # 可选，该会话的默认 system prompt


class SessionResponse(BaseModel):
    """会话列表/详情响应"""
    id: str
    title: str
    system_prompt: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    message_count: Optional[int] = None   # 消息数量（列表接口中返回，COUNT 子查询结果）

    # 序列化时确保 datetime 带 UTC 时区标识（SQLite 存储会丢失 tzinfo）
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
