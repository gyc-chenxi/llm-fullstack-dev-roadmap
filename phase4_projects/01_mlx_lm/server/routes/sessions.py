"""
会话 CRUD RESTful API
---------------------
提供会话的创建、查询、删除，以及消息历史的查询。

数据流向：
  GET    /api/sessions                   → SessionResponse[]     （全部会话，按updated_at倒序）
  POST   /api/sessions                   → SessionResponse       （创建新会话）
  GET    /api/sessions/{id}              → SessionResponse       （单个会话详情）
  DELETE /api/sessions/{id}              → 204 No Content         （级联删除会话+消息）
  GET    /api/sessions/{id}/messages     → MessageResponse[]      （会话的完整消息历史）
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session as DBSession, select, delete, func

from database import get_db
from models import ChatSession, Message
from schemas import SessionCreate, SessionResponse, MessageResponse

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


# ---------------------------------------------------------------------------
# GET /api/sessions — 获取所有会话列表（按更新时间倒序）
# ---------------------------------------------------------------------------
@router.get("", response_model=list[SessionResponse])
def list_sessions(db: DBSession = Depends(get_db)):
    """
    返回所有会话，按 updated_at 倒序（最近更新的排最前）。
    附带每个会话的消息数量（COUNT 子查询，避免全量加载消息到内存）。
    """
    statement = select(ChatSession).order_by(ChatSession.updated_at.desc())
    sessions = db.exec(statement).all()

    result = []
    for s in sessions:
        # 使用 func.count() 执行 COUNT(*)，不加载完整消息列表
        count_stmt = select(func.count()).select_from(Message).where(Message.session_id == s.id)
        msg_count = db.exec(count_stmt).one()

        result.append(
            SessionResponse(
                id=s.id,
                title=s.title,
                system_prompt=s.system_prompt,
                created_at=s.created_at,
                updated_at=s.updated_at,
                message_count=msg_count,
            )
        )
    return result


# ---------------------------------------------------------------------------
# POST /api/sessions — 创建新会话
# ---------------------------------------------------------------------------
@router.post("", response_model=SessionResponse, status_code=201)
def create_session(body: SessionCreate, db: DBSession = Depends(get_db)):
    """
    创建一个新的空会话。
    标题和 system_prompt 可选，不传则使用 "新对话" 默认标题。
    """
    now = datetime.now(timezone.utc)
    new_session = ChatSession(
        id=str(uuid.uuid4()),
        title=body.title or "新对话",
        system_prompt=body.system_prompt,
        created_at=now,
        updated_at=now,
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    return SessionResponse(
        id=new_session.id,
        title=new_session.title,
        system_prompt=new_session.system_prompt,
        created_at=new_session.created_at,
        updated_at=new_session.updated_at,
        message_count=0,
    )


# ---------------------------------------------------------------------------
# GET /api/sessions/{session_id} — 获取单个会话详情
# ---------------------------------------------------------------------------
@router.get("/{session_id}", response_model=SessionResponse)
def get_session(session_id: str, db: DBSession = Depends(get_db)):
    """
    返回指定会话的元信息（含消息数量）。
    会话不存在返回 404。
    """
    session = db.get(ChatSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    count_stmt = select(func.count()).select_from(Message).where(Message.session_id == session.id)
    msg_count = db.exec(count_stmt).one()

    return SessionResponse(
        id=session.id,
        title=session.title,
        system_prompt=session.system_prompt,
        created_at=session.created_at,
        updated_at=session.updated_at,
        message_count=msg_count,
    )


# ---------------------------------------------------------------------------
# DELETE /api/sessions/{session_id} — 删除会话及其所有消息
# ---------------------------------------------------------------------------
@router.delete("/{session_id}", status_code=204)
def delete_session(session_id: str, db: DBSession = Depends(get_db)):
    """
    删除指定会话，级联删除其所有消息。
    先显式 delete(Message) 再 delete(ChatSession) — ORM cascade 保底，显式删除更安全。
    会话不存在返回 404。
    """
    session = db.get(ChatSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    # 显式删除关联消息（ORM cascade 应自动处理，但显式操作更可靠）
    db.exec(delete(Message).where(Message.session_id == session_id))
    db.delete(session)
    db.commit()
    return None  # 204 No Content


# ---------------------------------------------------------------------------
# GET /api/sessions/{session_id}/messages — 获取某个会话的全部消息
# ---------------------------------------------------------------------------
@router.get("/{session_id}/messages", response_model=list[MessageResponse])
def get_messages(session_id: str, db: DBSession = Depends(get_db)):
    """
    返回指定会话的所有消息，按 created_at 正序排列（最早的在前）。
    前端据此顺序渲染对话气泡。
    会话不存在返回 404。
    """
    # 验证会话存在
    session = db.get(ChatSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    # 按创建时间正序查询
    statement = (
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.asc())
    )
    messages = db.exec(statement).all()

    return [
        MessageResponse(
            id=m.id,
            session_id=m.session_id,
            role=m.role,
            content=m.content,
            created_at=m.created_at,
        )
        for m in messages
    ]
