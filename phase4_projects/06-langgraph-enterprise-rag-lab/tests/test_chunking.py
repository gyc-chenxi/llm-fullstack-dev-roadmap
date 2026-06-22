"""Unit tests for text chunking."""

from __future__ import annotations

import sys
from pathlib import Path

# Allow pytest to find the src package.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest
from langgraph_enterprise_rag.retrieval.chunking import chunk_text, normalize_text


def test_normalize_removes_empty_lines() -> None:
    result = normalize_text("hello\n\n\nworld\n  ")
    assert "hello" in result
    assert "world" in result
    # No blank lines should remain.
    assert "\n\n" not in result


def test_normalize_preserves_single_newlines() -> None:
    result = normalize_text("line1\nline2\nline3")
    lines = result.splitlines()
    assert len(lines) == 3


def test_chunk_basic() -> None:
    text = "ABC" * 500  # 1500 chars
    chunks = chunk_text(text, chunk_size=300, chunk_overlap=30)
    assert len(chunks) >= 4
    # Every chunk should be non-empty.
    for c in chunks:
        assert len(c) > 0


def test_chunk_empty_text() -> None:
    assert chunk_text("") == []
    assert chunk_text("   \n  ") == []


def test_chunk_overlap_smaller_than_size() -> None:
    with pytest.raises(ValueError, match="chunk_overlap"):
        chunk_text("hello world", chunk_size=10, chunk_overlap=10)


def test_chunk_size_must_be_positive() -> None:
    with pytest.raises(ValueError, match="positive"):
        chunk_text("hello world", chunk_size=0)


def test_short_text_single_chunk() -> None:
    chunks = chunk_text("short text", chunk_size=700, chunk_overlap=120)
    assert len(chunks) == 1
    assert chunks[0] == "short text"


def test_chunk_overlap_content() -> None:
    """Verify that consecutive chunks share some content."""
    text = "0123456789" * 20  # 200 chars
    chunks = chunk_text(text, chunk_size=50, chunk_overlap=10)
    if len(chunks) >= 2:
        # The end of chunk[0] should appear near the start of chunk[1].
        tail = chunks[0][-10:]
        assert tail in chunks[1], f"Expected overlap content missing"
