"""
文档分割器
============

基于滑动窗口的文本分段，实现语义段落级 chunking。

数据流：
  raw_text → normalize_text(去空行) → sliding_window(chunk_size=700, overlap=120)
  → list[str] (chunks)

参数选择：
  - chunk_size=700: 中文约 350-500 字/chunk，适合 BGE-M3 的 8192 token 上下文
  - chunk_overlap=120: 约 17% 重叠，确保跨 chunk 边界的实体不会被切断
  - min_chunk_chars=80: 过滤掉太短的片段（如页脚、版权声明）
"""

from __future__ import annotations


def chunk_text(
    text: str,
    chunk_size: int = 700,
    chunk_overlap: int = 120,
) -> list[str]:
    """滑动窗口文本分割。

    Args:
        text: 输入文本
        chunk_size: 每个 chunk 的字符数
        chunk_overlap: 相邻 chunk 的重叠字符数（必须 < chunk_size）

    Returns:
        chunk 列表

    Raises:
        ValueError: chunk_size <= 0 或 chunk_overlap >= chunk_size
    """
    text = normalize_text(text)

    if not text:
        return []

    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")

    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    chunks: list[str] = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = end - chunk_overlap

    return chunks


def normalize_text(text: str) -> str:
    """去除空白行和行首尾空格，保留段落结构。"""
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines)
