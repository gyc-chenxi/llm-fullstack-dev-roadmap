"""
API 冒烟测试
===============

使用 FastAPI TestClient 验证路由注册和请求验证（不需要 LLM/Chroma 运行时）。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest
from fastapi.testclient import TestClient

from langgraph_enterprise_rag.api.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    """health 端点返回 200 + status=ok。"""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


def test_rag_invoke_schema_validation() -> None:
    """Pydantic 验证：缺失字段和空字段均应返回 422。"""
    resp = client.post("/v1/rag/invoke", json={})
    assert resp.status_code == 422

    resp = client.post(
        "/v1/rag/invoke",
        json={"query": "", "thread_id": "t1"},
    )
    assert resp.status_code == 422


def test_rag_invoke_minimal() -> None:
    """最小请求应返回 200/500/503（取决于 Chroma 是否就绪）。"""
    resp = client.post(
        "/v1/rag/invoke",
        json={
            "query": "这是一个测试问题",
            "thread_id": "smoke-test-001",
            "max_retries": 1,
        },
    )
    assert resp.status_code in (200, 500, 503)


def test_rag_stream_endpoint() -> None:
    """流式端点存在并可调用。"""
    resp = client.post(
        "/v1/rag/stream",
        json={
            "query": "测试流式输出",
            "thread_id": "stream-test-001",
        },
    )
    assert resp.status_code in (200, 500, 503)


def test_get_state_not_found() -> None:
    """查询不存在的 thread_id 返回 checkpoint_exists=False。"""
    resp = client.get("/v1/rag/state/nonexistent-thread-999")
    assert resp.status_code == 200
    data = resp.json()
    assert data["thread_id"] == "nonexistent-thread-999"
    assert data["checkpoint_exists"] is False
