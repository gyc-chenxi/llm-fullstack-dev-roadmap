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
    builder = StateGraph(RAGState)

    builder.add_node("classify", classify_node)
    builder.add_node("rewrite", rewrite_node)
    builder.add_node("retrieve", retrieve_node)
    builder.add_node("judge", judge_node)
    builder.add_node("rerank", rerank_node)
    builder.add_node("generate", generate_node)
    builder.add_node("verify", verify_node)
    builder.add_node("fallback", fallback_node)
    builder.add_node("output", output_node)

    builder.add_edge(START, "classify")
    builder.add_edge("classify", "rewrite")
    builder.add_edge("rewrite", "retrieve")
    builder.add_edge("retrieve", "judge")

    builder.add_conditional_edges(
        "judge",
        route_after_judge,
        {
            "rewrite": "rewrite",
            "rerank": "rerank",
            "fallback": "fallback",
        },
    )

    builder.add_edge("rerank", "generate")
    builder.add_edge("generate", "verify")

    builder.add_conditional_edges(
        "verify",
        route_after_verify,
        {
            "generate": "generate",
            "output": "output",
        },
    )

    builder.add_edge("fallback", "output")
    builder.add_edge("output", END)

    return builder.compile(checkpointer=checkpointer)