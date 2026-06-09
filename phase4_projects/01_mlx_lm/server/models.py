"""
数据库模型定义
--------------
使用 SQLModel：每个类同时是数据库表（继承 SQLModel）和 Pydantic 验证模型。

表结构：
  - ChatSession: 会话记录（id, title, system_prompt, created_at, updated_at）
  - Message:     对话消息（id, session_id, role, content, created_at）
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
    __tablename__ = "chat_sessions"

    # UUID 作为主键，避免自增 ID 的猜测风险
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True,
        max_length=36,
    )
    # 会话标题：自动取第一条用户消息的前 30 个字符
    title: str = Field(default="新对话", max_length=255)
    # 该会话使用的系统提示词
    system_prompt: Optional[str] = Field(default=None, sa_column=Column(SAText))
    # 时间戳
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        # sa_column_kwargs={"onupdate": datetime.now(timezone.utc)}  # SQLite 不原生支持
    )

    # 关联的消息列表（ORM 关系，非数据库列）
    messages: list["Message"] = Relationship(
        back_populates="session",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


# ---------------------------------------------------------------------------
# Message — 一条具体的对话消息
# ---------------------------------------------------------------------------
class Message(SQLModel, table=True):
    __tablename__ = "messages"

    # 自增主键（保证消息顺序）
    id: Optional[int] = Field(default=None, primary_key=True)
    # 外键 → ChatSession
    session_id: str = Field(foreign_key="chat_sessions.id", max_length=36)
    # 角色：system / user / assistant
    role: str = Field(max_length=16)
    # 消息正文（Markdown 格式）
    content: str = Field(sa_column=Column(SAText))
    # 消息时间戳
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    # 反向引用
    session: ChatSession = Relationship(back_populates="messages")
