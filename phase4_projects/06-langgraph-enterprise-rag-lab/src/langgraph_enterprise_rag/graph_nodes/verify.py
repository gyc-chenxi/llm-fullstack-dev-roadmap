"""
答案忠实性校验节点
=====================

启发式评估生成答案对检索文档的忠实性（不调用 LLM，纯规则评分）。

评分规则（按优先级递减）：
  1. 答句含"知识库中未找到足够证据" → 1.0（自认能力边界）
  2. 有引用标记 + 有来源 + 含"来源"字样 → 0.85（格式完整）
  3. 有引用标记 + 有来源（无"来源"字样）→ 0.72（格式部分完整）
  4. 否则 → 0.30（无法验证忠实性）

数据流：generated_answer + citations + docs → 启发式规则 → faithfulness_score
"""

from __future__ import annotations

from langgraph_enterprise_rag.graph.state import RAGState


def verify_node(state: RAGState) -> dict:
    """启发式评估答案忠实性，输出 0-1 分数。

    这是一个轻量级校验节点，不需要 LLM 调用。
    生产级系统可替换为 LLM-as-judge 或 NLI 模型。
    """
    answer = state.get("generated_answer", "")
    citations = state.get("citations", [])
    docs = state.get("reranked_docs") or state.get("retrieved_docs", [])

    if "知识库中未找到足够证据" in answer:
        score = 1.0  # 系统正确识别了自己的能力边界
    elif citations and docs and "来源" in answer:
        score = 0.85  # 引用格式完整
    elif citations and docs:
        score = 0.72  # 有引用但格式不完整
    else:
        score = 0.30  # 无法验证

    return {
        "faithfulness_score": score,
        "events": [
            {
                "node": "verify",
                "status": "done",
                "faithfulness_score": score,
            }
        ],
    }
