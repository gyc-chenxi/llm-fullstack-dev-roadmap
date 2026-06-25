"""
单元测试：文本分割（chunking）
==============================

测试 normalize_text 和 chunk_text 的正常路径和边界条件。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest
from langgraph_enterprise_rag.retrieval.chunking import chunk_text, normalize_text


def test_normalize_removes_empty_lines() -> None:
    """空白行被移除。"""
    result = normalize_text("hello\n\n\nworld\n  ")
    assert "hello" in result
    assert "world" in result
    assert "\n\n" not in result


def test_normalize_preserves_single_newlines() -> None:
    """正常换行被保留。"""
    result = normalize_text("line1\nline2\nline3")
    lines = result.splitlines()
    assert len(lines) == 3


def test_chunk_basic() -> None:
    """1500 字符文本按 300 切分 > 4 块。"""
    text = "ABC" * 500
    chunks = chunk_text(text, chunk_size=300, chunk_overlap=30)
    assert len(chunks) >= 4
    for c in chunks:
        assert len(c) > 0


def test_chunk_empty_text() -> None:
    """空文本返回空列表。"""
    assert chunk_text("") == []
    assert chunk_text("   \n  ") == []


def test_chunk_overlap_smaller_than_size() -> None:
    """overlap >= chunk_size 时抛出 ValueError。"""
    with pytest.raises(ValueError, match="chunk_overlap"):
        chunk_text("hello world", chunk_size=10, chunk_overlap=10)


def test_chunk_size_must_be_positive() -> None:
    """chunk_size <= 0 时抛出 ValueError。"""
    with pytest.raises(ValueError, match="positive"):
        chunk_text("hello world", chunk_size=0)


def test_short_text_single_chunk() -> None:
    """短文本保持为单个 chunk。"""
    chunks = chunk_text("short text", chunk_size=700, chunk_overlap=120)
    assert len(chunks) == 1
    assert chunks[0] == "short text"


def test_chunk_overlap_content() -> None:
    """相邻 chunk 应共享重叠区域的内容。"""
    text = "0123456789" * 20  # 200 chars
    chunks = chunk_text(text, chunk_size=50, chunk_overlap=10)
    if len(chunks) >= 2:
        tail = chunks[0][-10:]
        assert tail in chunks[1], f"Expected overlap content missing"
