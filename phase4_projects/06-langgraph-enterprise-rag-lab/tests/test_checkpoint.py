"""Unit tests for LangGraph checkpoint (offline, no API server needed)."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest
from langgraph_enterprise_rag.graph.builder import build_graph
from langgraph_enterprise_rag.graph.checkpoints import build_sqlite_checkpointer
from langgraph_enterprise_rag.graph.state import RAGState


@pytest.fixture()
def temp_checkpoint_db() -> str:
    """Create a temporary SQLite database for checkpoint tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.sqlite")
        old_db = os.environ.get("CHECKPOINT_DB")
        os.environ["CHECKPOINT_DB"] = db_path
        try:
            yield db_path
        finally:
            if old_db:
                os.environ["CHECKPOINT_DB"] = old_db
            else:
                del os.environ["CHECKPOINT_DB"]


def test_build_checkpointer_creates_db(temp_checkpoint_db: str) -> None:
    checkpointer = build_sqlite_checkpointer()
    assert checkpointer is not None
    assert os.path.exists(temp_checkpoint_db)


def test_graph_invoke_with_checkpoint(temp_checkpoint_db: str) -> None:
    """Invoke the graph with a checkpointer and verify state is saved."""
    checkpointer = build_sqlite_checkpointer()
    graph = build_graph(checkpointer=checkpointer)

    config = {"configurable": {"thread_id": "test-thread-001"}}

    result = graph.invoke(
        {
            "query": "RAG 是什么？",
            "thread_id": "test-thread-001",
            "max_retries": 3,
            "retrieve_retry_count": 0,
            "generate_retry_count": 0,
            "events": [],
            "errors": [],
        },
        config=config,
    )

    assert "query" in result or "final_answer" in result or "generated_answer" in result

    # Retrieve checkpoint state.
    state = graph.get_state(config)
    assert state is not None
    assert state.values is not None


def test_different_threads_isolated(temp_checkpoint_db: str) -> None:
    """Each thread_id should have its own checkpoint."""
    checkpointer = build_sqlite_checkpointer()
    graph = build_graph(checkpointer=checkpointer)

    t1 = {"configurable": {"thread_id": "thread-a"}}
    t2 = {"configurable": {"thread_id": "thread-b"}}

    graph.invoke(
        {
            "query": "query A",
            "thread_id": "thread-a",
            "max_retries": 3,
            "retrieve_retry_count": 0,
            "generate_retry_count": 0,
            "events": [],
            "errors": [],
        },
        config=t1,
    )

    graph.invoke(
        {
            "query": "query B",
            "thread_id": "thread-b",
            "max_retries": 3,
            "retrieve_retry_count": 0,
            "generate_retry_count": 0,
            "events": [],
            "errors": [],
        },
        config=t2,
    )

    s1 = graph.get_state(t1)
    s2 = graph.get_state(t2)

    assert s1 is not None
    assert s2 is not None
    # Different threads → different state snapshots.
    assert s1.values.get("query") != s2.values.get("query")  # type: ignore[union-attr]
