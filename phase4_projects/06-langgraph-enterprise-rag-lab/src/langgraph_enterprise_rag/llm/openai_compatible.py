from __future__ import annotations

import os

from langchain_openai import ChatOpenAI


def build_llm(
    temperature: float = 0.1,
    timeout: int = 120,
) -> ChatOpenAI:
    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "local-qwen2.5-7b-instruct"),
        base_url=os.getenv("OPENAI_API_BASE", "http://127.0.0.1:8080/v1"),
        api_key=os.getenv("OPENAI_API_KEY", "local"),
        temperature=temperature,
        timeout=timeout,
    )