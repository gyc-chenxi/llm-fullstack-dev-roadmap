"""
LangGraph 状态机构建器
========================

构建 8 节点 RAG 状态机，包括两类条件路由：

路由 1 (judge 后):
  - relevance_score >= 0.45 → rerank → generate → verify
  - relevance_score < 0.45 & retries left → rewrite (重新改写查询再检索)
  - relevance_score < 0.45 & retries exhausted → fallback (拒绝回答)

路由 2 (verify 后):
  - faithfulness_score >= 0.70 → output (生成答案通过校验)
  - faithfulness_score < 0.70 & retries left → generate (重新生成)
  - faithfulness_score < 0.70 & retries exhausted → output (强制输出)

可选的 checkpointer 参数用于 SQLite 持久化状态（支持断点恢复）。
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from langgraph_enterprise_rag.graph.routing import (
    route_after_judge,
    route_after_verify,
)
from langgraph_enterprise_rag.graph.state import RAGState
from langgraph_enterprise_rag.graph_nodes.classify import classify_node
from langgraph_enterprise_rag.graph_nodes.fallback import fallback_node
from langgraph_enterprise_rag.graph_nodes.generate import generate_node
from langgraph_enterprise_rag.graph_nodes.judge import judge_node
from langgraph_enterprise_rag.graph_nodes.output import output_node
from langgraph_enterprise_rag.graph_nodes.rerank import rerank_node
from langgraph_enterprise_rag.graph_nodes.retrieve import retrieve_node
from langgraph_enterprise_rag.graph_nodes.rewrite import rewrite_node
from langgraph_enterprise_rag.graph_nodes.verify import verify_node


def build_graph(checkpointer=None):
    """构建并编译 RAG 状态机。

    Args:
        checkpointer: 可选，SqliteSaver / AsyncSqliteSaver 实例，
                      用于将对话状态持久化到 SQLite

    Returns:
        CompiledGraph: 已编译的 LangGraph 图，可直接调用 .invoke() / .ainvoke()
    """
    builder = StateGraph(RAGState)

    # 注册 8 个节点
    builder.add_node("classify", classify_node)
    builder.add_node("rewrite", rewrite_node)
    builder.add_node("retrieve", retrieve_node)
    builder.add_node("judge", judge_node)
    builder.add_node("rerank", rerank_node)
    builder.add_node("generate", generate_node)
    builder.add_node("verify", verify_node)
    builder.add_node("fallback", fallback_node)
    builder.add_node("output", output_node)

    # 线性链路：classify → rewrite → retrieve → judge
    builder.add_edge(START, "classify")
    builder.add_edge("classify", "rewrite")
    builder.add_edge("rewrite", "retrieve")
    builder.add_edge("retrieve", "judge")

    # 条件路由 1：judge 根据相关性分数决定下一步
    builder.add_conditional_edges(
        "judge",
        route_after_judge,
        {
            "rewrite": "rewrite",   # 检索不相关，改写查询重试
            "rerank": "rerank",     # 检索相关，进入重排序
            "fallback": "fallback", # 多次重试失败，放弃
        },
    )

    builder.add_edge("rerank", "generate")
    builder.add_edge("generate", "verify")

    # 条件路由 2：verify 根据忠实性分数决定下一步
    builder.add_conditional_edges(
        "verify",
        route_after_verify,
        {
            "generate": "generate", # 答案不够忠实，重新生成
            "output": "output",     # 答案通过校验
        },
    )

    builder.add_edge("fallback", "output")
    builder.add_edge("output", END)

    return builder.compile(checkpointer=checkpointer)