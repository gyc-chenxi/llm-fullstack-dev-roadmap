"""
条件路由规则
==============

LangGraph 的两条条件路由边，每条路由根据 state 中的分数和重试计数决定
下一步执行哪个节点。

路由逻辑：
  route_after_judge(relevance_score, retry_count) → rerank / rewrite / fallback
  route_after_verify(faithfulness_score, retry_count) → output / generate

重试机制：
  - 检索阶段：最多 max_retries 次 rewrite→retrieve→judge 循环
  - 生成阶段：最多 max_retries 次 generate→verify 循环
  - 超过上限后强制下行（避免无限循环）
"""

from __future__ import annotations

from typing import Literal

from langgraph_enterprise_rag.graph.state import RAGState


def route_after_judge(state: RAGState) -> Literal["rewrite", "rerank", "fallback"]:
    """检索相关性判决后的路由。

    判决逻辑：
      - relevance_score >= 0.45 → 检索质量合格，进入 rerank 精排
      - relevance_score < 0.45 & retries left → 改写查询重新检索
      - relevance_score < 0.45 & retries exhausted → 放弃检索，走 fallback
    """
    score = float(state.get("relevance_score", 0.0))
    retry_count = int(state.get("retrieve_retry_count", 0))
    max_retries = int(state.get("max_retries", 3))

    if score >= 0.45:
        return "rerank"

    if retry_count < max_retries:
        return "rewrite"

    return "fallback"


def route_after_verify(state: RAGState) -> Literal["generate", "output"]:
    """答案忠实性校验后的路由。

    判决逻辑：
      - faithfulness_score >= 0.70 → 答案足够忠实，进入 output
      - faithfulness_score < 0.70 & retries left → 重新生成
      - faithfulness_score < 0.70 & retries exhausted → 强制输出（即使不够好）
    """
    score = float(state.get("faithfulness_score", 0.0))
    retry_count = int(state.get("generate_retry_count", 0))
    max_retries = int(state.get("max_retries", 3))

    if score >= 0.70:
        return "output"

    if retry_count < max_retries:
        return "generate"

    return "output"