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
            # 某些版本会自动 setup；这里兼容不同版本。
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
