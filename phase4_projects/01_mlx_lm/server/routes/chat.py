"""
聊天补全 SSE 端点
-----------------
OpenAI 兼容的 /v1/chat/completions 接口，带：
  1. 滑动窗口上下文截断（防止 OOM）
  2. 增量 delta SSE 流式输出（修复 mlx_lm 返回完整文本的 bug）
  3. 流结束后自动持久化 User 消息 + Assistant 完整回复到数据库
"""

import asyncio
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

from schemas import ChatRequest
from models import ChatSession, Message

router = APIRouter(prefix="/v1", tags=["chat"])


@router.post("/chat/completions")
async def chat_completions(req: ChatRequest, request: Request):
    """
    SSE 流式聊天补全端点。

    流程：
      1. 从 Request 获取 LLMEngine 实例
      2. 转化为 messages 列表
      3. LLMEngine.chat() 进行截断 + 流式生成（产出 delta）
      4. 流结束时持久化 user + assistant 消息到 SQLite
    """
    engine = request.app.state.engine

    # 将 ChatMessage 列表转为纯 dict 列表
    messages = [m.model_dump() for m in req.messages]

    # 自动添加系统提示词（如果提供了 system_prompt 参数但 messages 中没有 system 角色）
    if req.system_prompt and not any(m["role"] == "system" for m in messages):
        messages.insert(0, {"role": "system", "content": req.system_prompt})

    async def event_generator():
        full_response = ""  # 累积完整的 assistant 回复，用于持久化

        try:
            # 流式生成（engine.chat 内部已处理滑动窗口截断）
            for delta in engine.chat(
                messages,
                max_tokens=req.max_tokens,
                temperature=req.temperature,
                truncate=True,
            ):
                full_response += delta

                # 构建 OpenAI 兼容的 SSE chunk
                chunk = {
                    "id": f"chatcmpl-{id(full_response):x}",
                    "object": "chat.completion.chunk",
                    "created": int(datetime.now(timezone.utc).timestamp()),
                    "model": "qwen2.5-7b-instruct",
                    "choices": [
                        {
                            "index": 0,
                            "delta": {"content": delta},
                            "finish_reason": None,
                        }
                    ],
                }
                yield {"data": json.dumps(chunk, ensure_ascii=False)}
                await asyncio.sleep(0)  # 让出事件循环，避免阻塞

            # 发送结束信号（包含 finish_reason）
            final_chunk = {
                "id": f"chatcmpl-{id(full_response):x}",
                "object": "chat.completion.chunk",
                "created": int(datetime.now(timezone.utc).timestamp()),
                "model": "qwen2.5-7b-instruct",
                "choices": [
                    {
                        "index": 0,
                        "delta": {},
                        "finish_reason": "stop",
                    }
                ],
            }
            yield {"data": json.dumps(final_chunk, ensure_ascii=False)}
            yield {"data": "[DONE]"}

            # ---- 持久化到数据库 ----
            await _persist_messages(request, req, full_response, messages)

        except Exception as e:
            # 生成过程中出错 - 发送错误事件
            error_chunk = {"error": {"message": str(e), "type": "server_error"}}
            yield {"data": json.dumps(error_chunk, ensure_ascii=False)}
            yield {"data": "[DONE]"}
            raise

    return EventSourceResponse(event_generator())


# ---------------------------------------------------------------------------
# 持久化辅助函数
# ---------------------------------------------------------------------------

async def _persist_messages(
    request: Request,
    req: ChatRequest,
    full_response: str,
    messages: list[dict],
):
    """
    将用户提问和助手回复写入数据库。

    如果请求中没有 session_id，自动创建新会话。
    如果会话标题为空，自动取第一条用户消息的前 30 个字符作为标题。
    """
    from database import Session as DBSession  # SQLModel 的 ORM session

    with DBSession(request.app.state.engine.db_engine) as db:
        session_id = req.session_id

        # 如果没有传入 session_id，创建新会话
        if not session_id:
            import uuid
            session_id = str(uuid.uuid4())

            # 自动从第一条 user 消息生成标题
            title = "新对话"
            user_messages = [m for m in messages if m["role"] == "user"]
            if user_messages:
                first_content = user_messages[0]["content"]
                title = first_content[:30] + ("..." if len(first_content) > 30 else "")

            # 提取系统提示词
            system_prompt = None
            system_msgs = [m for m in messages if m["role"] == "system"]
            if system_msgs:
                system_prompt = system_msgs[0]["content"]

            new_session = ChatSession(
                id=session_id,
                title=title,
                system_prompt=system_prompt,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.add(new_session)
        else:
            # 更新已有会话的 updated_at
            existing = db.get(ChatSession, session_id)
            if existing:
                existing.updated_at = datetime.now(timezone.utc)
                db.add(existing)

        # 获取最后一条 user 消息
        last_user_msg = None
        for m in reversed(messages):
            if m["role"] == "user":
                last_user_msg = m
                break

        now = datetime.now(timezone.utc)

        # 保存 user 消息（如果本次请求中有）
        if last_user_msg:
            user_msg = Message(
                session_id=session_id,
                role="user",
                content=last_user_msg["content"],
                created_at=now,
            )
            db.add(user_msg)

        # 保存 assistant 回复
        if full_response:
            assistant_msg = Message(
                session_id=session_id,
                role="assistant",
                content=full_response,
                created_at=now,
            )
            db.add(assistant_msg)

        db.commit()
