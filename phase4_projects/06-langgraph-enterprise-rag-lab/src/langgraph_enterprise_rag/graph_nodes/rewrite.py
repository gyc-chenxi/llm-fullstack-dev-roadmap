from __future__ import annotations

import json
import re

from langchain_core.messages import HumanMessage, SystemMessage

from langgraph_enterprise_rag.graph.state import RAGState
from langgraph_enterprise_rag.llm.openai_compatible import build_llm


def rewrite_node(state: RAGState) -> dict:
    query = state["query"]
    retry_count = int(state.get("retrieve_retry_count", 0))

    llm = build_llm(temperature=0.1)

    system = SystemMessage(
        content=(
            "你是企业级 RAG 检索查询改写器。"
            "你只能输出 JSON 数组，不要解释。"
        )
    )

    human = HumanMessage(
        content=(
            "请把用户问题改写成 3 个适合知识库检索的查询变体。\n"
            "要求：保留核心实体；一个偏关键词；一个偏语义；一个偏中文完整问句。\n\n"
            f"用户问题：{query}\n\n"
            '输出示例：["查询1", "查询2", "查询3"]'
        )
    )

    try:
        result = llm.invoke([system, human]).content
        rewritten = extract_json_array(result)
    except Exception as exc:
        rewritten = [query]
        return {
            "rewritten_queries": rewritten,
            "retrieve_retry_count": retry_count + 1,
            "errors": [f"rewrite failed: {exc!r}"],
            "events": [{"node": "rewrite", "status": "fallback"}],
        }

    if not rewritten:
        rewritten = [query]

    if query not in rewritten:
        rewritten.insert(0, query)

    return {
        "rewritten_queries": rewritten[:4],
        "retrieve_retry_count": retry_count + 1,
        "events": [
            {
                "node": "rewrite",
                "status": "done",
                "rewritten_queries": rewritten[:4],
            }
        ],
    }


def extract_json_array(text: str) -> list[str]:
    text = text.strip()

    try:
        obj = json.loads(text)
        if isinstance(obj, list):
            return [str(x).strip() for x in obj if str(x).strip()]
    except Exception:
        pass

    match = re.search(r"\[[\s\S]*\]", text)
    if not match:
        return []

    try:
        obj = json.loads(match.group(0))
        if isinstance(obj, list):
            return [str(x).strip() for x in obj if str(x).strip()]
    except Exception:
        return []

    return []