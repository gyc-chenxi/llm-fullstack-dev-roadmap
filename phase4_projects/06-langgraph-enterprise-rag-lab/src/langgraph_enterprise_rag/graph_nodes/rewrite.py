"""
查询改写节点
===============

通过 LLM 将原始用户问题改写成 3 个适合知识库检索的查询变体：
  1. 关键词变体：蒸馏为关键术语组合
  2. 语义变体：用不同措辞表达相同语义
  3. 中文完整问句：保持自然语言风格

为什么要改写：
  - 用户查询往往是自然语言，不适合直接做关键词检索
  - 多角度改写增加召回率（dense + BM25 各用不同查询）
  - 中英文混合表达可能导致召回偏差

LLM 输出格式：JSON 数组 ["查询1", "查询2", "查询3"]
解析回退：JSON 解析失败 → 正则提取 [ ... ] → 保留原始查询

数据流：query → LLM → rewritten_queries (3+1 变体) → 写入 state
"""

from __future__ import annotations

import json
import re

from langchain_core.messages import HumanMessage, SystemMessage

from langgraph_enterprise_rag.graph.state import RAGState
from langgraph_enterprise_rag.llm.openai_compatible import build_llm


def rewrite_node(state: RAGState) -> dict:
    """使用 LLM 将用户问题改写成 3 个检索友好的变体。

    每次调用都会递增 retrieve_retry_count（用于 judge 的路由判断）。
    改写失败时回退为原始查询。
    """
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
        rewritten.insert(0, query)  # 保留原始查询放在第一位

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
    """从 LLM 输出中提取 JSON 数组。

    两层回退：
      1. 直接 json.loads (理想情况)
      2. 正则匹配第一个 [... ] 块（容错 LLM 多输出括号外文本）
    """
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
