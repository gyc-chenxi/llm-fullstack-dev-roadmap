"""
FastAPI 应用入口
===================

LangGraph Enterprise RAG 的主要 API 服务（端口 8006）。

三层架构：
  Client → FastAPI (8006) → LangGraph StateGraph → llama.cpp (8080)

三个核心端点：
  - POST /v1/rag/invoke — 非流式 RAG 查询
  - POST /v1/rag/stream  — SSE 流式 RAG 查询（逐节点推送事件）
  - GET  /v1/rag/state/{thread_id} — 查询 checkpoint 状态

生命周期（AsyncSqliteSaver）：
  lifespan 中创建 AsyncSqliteSaver → 编译图 → 注入 app.state.graph
  退出时自动关闭数据库连接

为什么不使用模块顶层的 checkpointer：
  AsyncSqliteSaver 必须在 async context manager 内部保持连接，
  放在模块顶层会在 uvicorn import 时创建，导致不可预测的连接生命周期。
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from langgraph_enterprise_rag.api.schemas import RAGRequest
from langgraph_enterprise_rag.api.sse import sse_event
from langgraph_enterprise_rag.graph.builder import build_graph
from langgraph_enterprise_rag.retrieval.chroma_store import build_chroma_store


NODE_NAMES = {
    "classify",
    "rewrite",
    "retrieve",
    "judge",
    "rerank",
    "generate",
    "verify",
    "fallback",
    "output",
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI 生命周期内持有 AsyncSqliteSaver。

    关键点：
    1. astream_events / ainvoke 必须搭配 AsyncSqliteSaver。
    2. AsyncSqliteSaver 必须在 async context manager 生命周期内保持打开。
    3. 不要在模块顶层直接创建异步 checkpointer，否则连接生命周期容易错。
    """
    db_path = Path(os.getenv("CHECKPOINT_DB", "data/checkpoints/langgraph.sqlite"))
    db_path.parent.mkdir(parents=True, exist_ok=True)

    async with AsyncSqliteSaver.from_conn_string(str(db_path)) as checkpointer:
        try:
            await checkpointer.setup()
        except Exception:
            pass

        app.state.graph = build_graph(checkpointer=checkpointer)

        try:
            store = build_chroma_store()
            print("LangGraph compiled with Async SQLite checkpoint")
            print(f"Chroma collection ready: enterprise_rag_docs, count={store.count()}")
        except Exception as exc:
            print(f"[startup][warn] Chroma not ready: {exc!r}")

        yield


app = FastAPI(
    title="LangGraph Enterprise RAG",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/v1/rag/invoke")
async def invoke_rag(req: RAGRequest, request: Request):
    """非流式 RAG 查询。

    数据流：
      RAGRequest JSON → graph.ainvoke(initial_state, config)
        → 8 节点全流程执行
        → RAGResp 结构化 JSON
    """
    graph = request.app.state.graph
    config = {"configurable": {"thread_id": req.thread_id}}

    result = await graph.ainvoke(
        {
            "query": req.query,
            "thread_id": req.thread_id,
            "max_retries": req.max_retries,
            "retrieve_retry_count": 0,
            "generate_retry_count": 0,
            "events": [],
            "errors": [],
        },
        config=config,
    )

    return {
        "thread_id": req.thread_id,
        "status": result.get("status", "ok"),
        "answer": result.get("final_answer") or result.get("generated_answer", ""),
        "citations": result.get("citations", []),
        "debug": {
            "query_type": result.get("query_type"),
            "rewritten_queries": result.get("rewritten_queries", []),
            "relevance_score": result.get("relevance_score"),
            "faithfulness_score": result.get("faithfulness_score"),
            "retrieve_retry_count": result.get("retrieve_retry_count"),
            "generate_retry_count": result.get("generate_retry_count"),
            "errors": result.get("errors", []),
            "events": result.get("events", []),
        },
    }


@app.post("/v1/rag/stream")
async def stream_rag(req: RAGRequest, request: Request):
    """SSE 流式 RAG 查询。

    数据流：
      graph.astream_events(inputs, version="v2")
        → 每个节点 on_chain_start 时推送 "node_start" SSE
        → 每个节点 on_chain_end 时推送 "node_end" SSE（含节点输出）
        → 所有节点完成后推送 "final" SSE（含完整答案和引用）
        → 异常时推送 "error" SSE
    """
    graph = request.app.state.graph
    config = {"configurable": {"thread_id": req.thread_id}}

    inputs = {
        "query": req.query,
        "thread_id": req.thread_id,
        "max_retries": req.max_retries,
        "retrieve_retry_count": 0,
        "generate_retry_count": 0,
        "events": [],
        "errors": [],
    }

    async def event_generator():
        yield sse_event(
            "node_start",
            {
                "node": "graph",
                "status": "running",
                "thread_id": req.thread_id,
            },
        )

        try:
            async for event in graph.astream_events(
                inputs,
                config=config,
                version="v2",
            ):
                kind = event.get("event")
                name = event.get("name")

                if name not in NODE_NAMES:
                    continue

                if kind == "on_chain_start":
                    yield sse_event(
                        "node_start",
                        {
                            "node": name,
                            "status": "running",
                        },
                    )

                elif kind == "on_chain_end":
                    data = event.get("data", {})
                    output = data.get("output", {})

                    payload = {
                        "node": name,
                        "status": "done",
                    }

                    if isinstance(output, dict):
                        for key in [
                            "query_type",
                            "rewritten_queries",
                            "relevance_score",
                            "faithfulness_score",
                            "status",
                        ]:
                            if key in output:
                                payload[key] = output[key]

                        if "retrieved_docs" in output:
                            payload["doc_count"] = len(output["retrieved_docs"])

                        if "reranked_docs" in output:
                            payload["doc_count"] = len(output["reranked_docs"])

                    yield sse_event("node_end", payload)

            latest = await graph.aget_state(config)
            values = latest.values if latest else {}

            yield sse_event(
                "final",
                {
                    "thread_id": req.thread_id,
                    "status": values.get("status", "ok"),
                    "answer": values.get("final_answer")
                    or values.get("generated_answer", ""),
                    "citations": values.get("citations", []),
                },
            )

        except Exception as exc:
            yield sse_event(
                "error",
                {
                    "thread_id": req.thread_id,
                    "message": repr(exc),
                },
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )


@app.get("/v1/rag/state/{thread_id}")
async def get_state(thread_id: str, request: Request):
    """查询指定 thread_id 的 checkpoint 状态。

    用于调试和审计：验证某个对话的完整 graph 执行路径。
    """
    graph = request.app.state.graph
    config = {"configurable": {"thread_id": thread_id}}
    state = await graph.aget_state(config)

    values = state.values if state else {}

    return {
        "thread_id": thread_id,
        "checkpoint_exists": bool(values),
        "latest_node": values.get("events", [{}])[-1].get("node")
        if values.get("events")
        else None,
        "values": values,
    }
