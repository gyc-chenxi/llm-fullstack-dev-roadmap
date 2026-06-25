"""
查询分类节点
===============

将用户查询分为三类：
  - multi_hop: 含"对比/综合/分别/关系/区别/影响/原因"等关键词，需多跳推理
  - needs_retrieval: 含"文档/知识库/资料/引用/根据/总结"等关键词，需检索
  - simple: 闲聊类，暂不触发检索（当前版本默认为 needs_retrieval）

数据流：query (str) → 关键词匹配 → query_type (Literal) → 写入 state
"""

from __future__ import annotations

from langgraph_enterprise_rag.graph.state import RAGState


def classify_node(state: RAGState) -> dict:
    """规则关键词分类器，将查询映射到三类之一。"""
    query = state.get("query", "").strip()

    if not query:
        return {
            "query_type": "simple",
            "errors": ["empty query"],
            "events": [{"node": "classify", "status": "failed"}],
        }

    retrieval_keywords = [
        "文档",
        "知识库",
        "资料",
        "引用",
        "根据",
        "总结",
        "解释",
        "对比",
        "来源",
        "报告",
    ]

    multi_hop_keywords = ["对比", "综合", "分别", "关系", "区别", "影响", "原因"]

    if any(word in query for word in multi_hop_keywords):
        query_type = "multi_hop"
    elif any(word in query for word in retrieval_keywords):
        query_type = "needs_retrieval"
    else:
        query_type = "needs_retrieval"  # 默认触发检索，避免遗漏

    return {
        "query_type": query_type,
        "events": [
            {
                "node": "classify",
                "status": "done",
                "query_type": query_type,
            }
        ],
    }
