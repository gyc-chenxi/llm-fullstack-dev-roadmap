"""
数据库模型定义
--------------
使用 SQLModel：每个类同时是数据库表（继承 SQLModel）和 Pydantic 验证模型。

表结构：
  chat_sessions (1) ──── (N) messages
    ChatSession: 会话记录（id, title, system_prompt, created_at, updated_at）
    Message:     对话消息（id, session_id, role, content, created_at）

CRUD 说明：
  - ChatSession.id 使用 UUID v4 主键，避免自增 ID 的信息泄露风险
  - Message.id 使用自增主键，确保消息的写入顺序
  - session_id 外键设置 cascade="all, delete-orphan"，删除会话时级联删除消息
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import Column, Text as SAText


# ---------------------------------------------------------------------------
# ChatSession — 一次完整的对话会话
# ---------------------------------------------------------------------------
class ChatSession(SQLModel, table=True):
    """会话表：记录一次连续对话的元信息"""
    __tablename__ = "chat_sessions"

    # UUID 主键（避免自增 ID 被猜测），前端通过此 ID 恢复对话上下文
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True,
        max_length=36,
    )
    # 会话标题：首次发送时自动取第一条 user 消息的前 30 个字符
    title: str = Field(default="新对话", max_length=255)
    # 该会话使用的系统提示词（从首次请求中提取）
    system_prompt: Optional[str] = Field(default=None, sa_column=Column(SAText))
    # 创建时间戳
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    # 最后更新时间（每次发送消息时更新，用于会话列表排序）
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        # sa_column_kwargs={"onupdate": datetime.now(timezone.utc)}  # SQLite 不原生支持 onupdate，故在应用层手动更新
    )

    # ORM 关系：该会话下的所有消息，级联删除
    messages: list["Message"] = Relationship(
        back_populates="session",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


# ---------------------------------------------------------------------------
# Message — 一条具体的对话消息
# ---------------------------------------------------------------------------
class Message(SQLModel, table=True):
    """消息表：记录单条对话内容"""
    __tablename__ = "messages"

    # 自增主键（保证消息在会话内的写入顺序）
    id: Optional[int] = Field(default=None, primary_key=True)
    # 所属会话 ID（外键 → chat_sessions.id）
    session_id: str = Field(foreign_key="chat_sessions.id", max_length=36)
    # 角色：system / user / assistant
    role: str = Field(max_length=16)
    # 消息正文（Markdown 格式，从模型返回后直接存储）
    content: str = Field(sa_column=Column(SAText))
    # 消息时间戳
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    # 反向引用：所属的会话
    session: ChatSession = Relationship(back_populates="messages")
