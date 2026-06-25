"""
优雅降级节点
===============

当多次检索重试仍无法找到相关知识时，系统统一拒绝回答。

为什么要拒绝而不是强行编造：
  - LLM 在无资料时会基于参数知识"编造"答案（幻觉）
  - 企业级 RAG 要求所有答案可溯源到知识库
  - 明确的能力边界声明比不可靠的答案更有价值

数据流：state (任意状态，通常来自 judge 重试耗尽) → fallback 固定文案
"""

from __future__ import annotations

from langgraph_enterprise_rag.graph.state import RAGState


def fallback_node(state: RAGState) -> dict:
    """返回统一的拒绝回答文案，state 设置为 fallback。"""
    answer = (
        "知识库中未找到足够证据回答该问题。\n\n"
        "为了避免幻觉，本系统不会基于模型自身知识强行编造答案。"
    )

    return {
        "generated_answer": answer,
        "citations": [],
        "status": "fallback",
        "events": [{"node": "fallback", "status": "done"}],
    }
