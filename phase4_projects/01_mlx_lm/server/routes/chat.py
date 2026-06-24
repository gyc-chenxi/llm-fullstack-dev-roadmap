"""
聊天补全 SSE 端点
-----------------
OpenAI 兼容的 /v1/chat/completions 接口。

数据流向：
  客户端 POST 请求 (ChatRequest)                      ← {messages, session_id, ...}
    → EventSourceResponse(event_generator)            ← SSE 流式响应
      → LLMEngine.chat(messages)                      ← 滑动窗口截断 + 模型推理
        → yield delta (str)                           ← 逐 token 文本增量
      → _persist_messages()                           ← 流结束后异步写入 SQLite

SSE 格式：data: {"choices": [{"delta": {"content": "..."}, "finish_reason": null}]}
           data: {"choices": [{"delta": {}, "finish_reason": "stop"}]}
           data: [DONE]
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
      1. 从 request.app.state 获取 LLMEngine 单例
      2. 将 Pydantic ChatMessage 列表转为纯 dict 列表，传入引擎
      3. 引擎内部自动执行：滑动窗口截断 → chat_template 拼接 → 逐 token 推理
      4. 每生成一个 token，立即构建 OpenAI 兼容的 SSE chunk 并推送
      5. 流结束时，异步持久化 user + assistant 消息到 SQLite

    参数：
      req: ChatRequest — Pydantic 校验后的请求体（messages, max_tokens, temperature, session_id）
      request: FastAPI Request — 用于访问 app.state

    返回：
      EventSourceResponse — SSE 流式响应（Content-Type: text/event-stream）
    """
    engine = request.app.state.engine

    # 将 Pydantic 模型转为纯 dict 列表：前端 tokenization 的输入
    # 格式：[{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
    messages = [m.model_dump() for m in req.messages]

    # 如果请求中传入了 system_prompt 参数且 messages 中没有 system 角色，
    # 自动插入到消息列表最前面
    if req.system_prompt and not any(m["role"] == "system" for m in messages):
        messages.insert(0, {"role": "system", "content": req.system_prompt})

    async def event_generator():
        """SSE 事件生成器：逐 token 流式推送，流结束持久化。"""
        full_response = ""  # 累积完整的 assistant 回复文本，用于最终持久化

        try:
            # 调用 LLMEngine.chat() 逐 token 生成（内部已处理滑动窗口截断）
            for delta in engine.chat(
                messages,
                max_tokens=req.max_tokens,
                temperature=req.temperature,
                truncate=True,
            ):
                full_response += delta

                # 构建 OpenAI 兼容的 SSE chunk
                # 参考 OpenAI 文档：https://platform.openai.com/docs/api-reference/chat/streaming
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
                await asyncio.sleep(0)  # 让出事件循环，避免 asyncio 协程饥饿

            # 发送结束 chunk（finish_reason: "stop"）
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
            yield {"data": "[DONE]"}  # SSE 流结束标记（按 OpenAI 惯例）

            # ---- 流结束后持久化到数据库 ----
            await _persist_messages(request, req, full_response, messages)

        except Exception as e:
            # 推理过程中出错：发送错误事件，防止客户端一直等待
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
    将本次对话的 user 消息和 assistant 回复写入 SQLite。

    策略：
      1. 如果 req.session_id 为空，自动创建新 ChatSession（UUID v4）
         - 自动取第一条 user 消息的前 30 字作为会话标题
         - 自动提取 system_prompt 存入会话
      2. 如果已存在 session_id，仅更新 updated_at 时间戳
      3. 分别写入最后一条 user 消息和完整 assistant 回复

    参数：
      request:      FastAPI Request（从中获取 db_engine）
      req:          原始请求体（含 session_id）
      full_response: 累积的完整 assistant 回复文本
      messages:     本次推理使用的消息列表（含已插入的 system prompt）
    """
    from database import Session as DBSession

    with DBSession(request.app.state.engine.db_engine) as db:
        session_id = req.session_id

        # -- 会话管理：没有 session_id 则新建 --
        if not session_id:
            import uuid
            session_id = str(uuid.uuid4())

            # 自动生成标题：取第一条 user 消息的前 30 个字符
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
            # 更新已有会话的更新时间为当前时间
            existing = db.get(ChatSession, session_id)
            if existing:
                existing.updated_at = datetime.now(timezone.utc)
                db.add(existing)

        # -- 消息持久化 --
        # 取出消息列表中的最后一条 user 消息（当前提问）
        last_user_msg = None
        for m in reversed(messages):
            if m["role"] == "user":
                last_user_msg = m
                break

        now = datetime.now(timezone.utc)

        # 写入 user 消息
        if last_user_msg:
            user_msg = Message(
                session_id=session_id,
                role="user",
                content=last_user_msg["content"],
                created_at=now,
            )
            db.add(user_msg)

        # 写入 assistant 完整回复
        if full_response:
            assistant_msg = Message(
                session_id=session_id,
                role="assistant",
                content=full_response,
                created_at=now,
            )
            db.add(assistant_msg)

        db.commit()
