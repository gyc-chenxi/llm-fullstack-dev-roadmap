"""
输出节点
===========

将 generated_answer 映射为 final_answer，确定最终 status。

这是 RAG 管线的终点节点，负责：
  1. 将中间生成的答案提升为最终输出
  2. 保持 status 状态透传（ok / fallback / failed）
  3. 附加 output 事件用于可观测性

数据流：generated_answer + status → final_answer (透传) → END
"""

from __future__ import annotations

from langgraph_enterprise_rag.graph.state import RAGState


def output_node(state: RAGState) -> dict:
    """将 generated_answer 提升为最终输出。"""
    status = state.get("status") or "ok"
    answer = state.get("generated_answer") or "未生成答案。"

    return {
        "final_answer": answer,
        "status": status,
        "events": [
            {
                "node": "output",
                "status": status,
            }
        ],
    }
