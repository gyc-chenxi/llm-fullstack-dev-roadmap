"""
RAG 答案生成节点
===================

基于 reranked_docs（top-5）调用 LLM 生成带引用的中文答案。

数据流：
  reranked_docs (5) → build_context() → 格式化上下文
    └→ [来源1] title: xxx source: xxx content: xxx (截断 1800 字符)
    └→ SystemMessage("企业级 RAG 问答系统") + HumanMessage(query + context)
    └→ LLM (ChatOpenAI, temperature=0.1) → answer (含 [来源N] 引用标记)
    └→ citations: [{label, doc_id, source, title, quote(前 220 字符)}]

关键约束：
  - 每个文档最多 1800 字符上下文（防止超过 LLM 上下文窗口）
  - max 5 docs → 最多 ~9000 字符上下文
  - LLM 被要求必须基于资料回答，资料不足时明确表达
"""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from langgraph_enterprise_rag.graph.state import RAGState
from langgraph_enterprise_rag.llm.openai_compatible import build_llm


def generate_node(state: RAGState) -> dict:
    """基于检索到的文档生成带引用的答案。

    优先使用 reranked_docs，回退 retrieved_docs。
    无文档时直接返回 fallback 文案。
    """
    query = state["query"]
    docs = state.get("reranked_docs") or state.get("retrieved_docs", [])[:5]
    retry_count = int(state.get("generate_retry_count", 0))

    if not docs:
        return {
            "generated_answer": "知识库中未找到足够证据回答该问题。",
            "citations": [],
            "generate_retry_count": retry_count + 1,
            "events": [{"node": "generate", "status": "no_context"}],
        }

    context = build_context(docs)

    llm = build_llm(temperature=0.1)

    system = SystemMessage(
        content=(
            "你是企业级 RAG 问答系统。"
            "必须只基于给定资料回答。"
            "如果资料不足，必须明确说"知识库中未找到足够证据"。"
            "每个关键结论后必须使用 [来源1]、[来源2] 这样的引用标记。"
        )
    )

    human = HumanMessage(
        content=(
            f"用户问题：{query}\n\n"
            f"资料：\n{context}\n\n"
            "请输出结构清晰、简洁、带引用的中文答案。"
        )
    )

    try:
        answer = llm.invoke([system, human]).content.strip()
    except Exception as exc:
        return {
            "generated_answer": "LLM 服务调用失败，无法生成答案。",
            "citations": [],
            "generate_retry_count": retry_count + 1,
            "errors": [f"generate failed: {exc!r}"],
            "events": [{"node": "generate", "status": "failed"}],
        }

    citations = []

    for idx, doc in enumerate(docs, start=1):
        citations.append(
            {
                "label": f"来源{idx}",
                "doc_id": doc.get("doc_id", ""),
                "source": doc.get("source", ""),
                "title": doc.get("title", ""),
                "quote": doc.get("content", "")[:220],
            }
        )

    return {
        "generated_answer": answer,
        "citations": citations,
        "generate_retry_count": retry_count + 1,
        "events": [
            {
                "node": "generate",
                "status": "done",
                "citation_count": len(citations),
            }
        ],
    }


def build_context(docs: list[dict]) -> str:
    """将检索文档列表格式化为 LLM 可理解的上下文文本。

    输出格式：
      [来源1]
      title: <title>
      source: <source>
      content:
      <content truncated to 1800 chars>
      ---
      [来源2]
      ...
    """
    parts = []

    for idx, doc in enumerate(docs[:5], start=1):
        content = doc.get("content", "")[:1800]
        source = doc.get("source", "")
        title = doc.get("title", "")

        parts.append(
            f"[来源{idx}]\n"
            f"title: {title}\n"
            f"source: {source}\n"
            f"content:\n{content}"
        )

    return "\n\n---\n\n".join(parts)
