"""
LLM 客户端（OpenAI Compatible）
=================================

通过 openai-compatible API (llama.cpp server, port 8080) 调用本地大模型。

数据流：
  build_llm() → ChatOpenAI(model, base_url, api_key, temperature, timeout)
    → LangChain Messages → openai-compatible HTTP POST → llama.cpp
    → Streaming / Non-streaming response → ChatMessage.content

为什么用 llama.cpp 而非直接加载模型：
  - llama.cpp 提供成熟的量化推理（GGUF 格式）
  - 解耦 LLM 推理和 RAG 管线，各服务可独立扩缩
  - API 兼容 OpenAI 格式，便于后续切换后端
"""

from __future__ import annotations

import os

from langchain_openai import ChatOpenAI


def build_llm(
    temperature: float = 0.1,
    timeout: int = 120,
) -> ChatOpenAI:
    """构建 OpenAI-compatible LLM 客户端。

    temperature=0.1: 低温度确保答案稳定性（接近确定性输出），
    但保留 0.1 的微小随机性以生成多样化的查询改写。

    timeout=120: VLM/RAG 推理在 7B 量化模型上可能需要 30-90s，
    留足 2 分钟避免超时。
    """
    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "local-qwen2.5-7b-instruct"),
        base_url=os.getenv("OPENAI_API_BASE", "http://127.0.0.1:8080/v1"),
        api_key=os.getenv("OPENAI_API_KEY", "local"),
        temperature=temperature,
        timeout=timeout,
    )
