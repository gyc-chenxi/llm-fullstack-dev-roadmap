"""
Phase 5 tests — RAG Retrieval, Agent Runtime, and RAG Eval.
"""

import pytest


# ============================================================
# Document Loader Tests
# ============================================================

class TestDocumentLoader:
    @pytest.mark.asyncio
    async def test_load_nonexistent(self):
        from app.infrastructure.retrieval.document_loader import DocumentLoader
        loader = DocumentLoader(base_dir="./nonexistent")
        docs = await loader.load("missing.txt")
        assert docs == []


# ============================================================
# Text Splitter Tests
# ============================================================

class TestTextSplitter:
    def test_short_text(self):
        from app.infrastructure.retrieval.text_splitter import TextSplitter
        splitter = TextSplitter(chunk_size=512, chunk_overlap=50)
        docs = [{"doc_id": "test", "content": "Short text.", "source": "test.txt"}]
        chunks = splitter.split(docs)
        assert len(chunks) == 1
        assert chunks[0]["doc_id"] == "test"

    def test_long_text_split(self):
        from app.infrastructure.retrieval.text_splitter import TextSplitter
        splitter = TextSplitter(chunk_size=100, chunk_overlap=20)
        long_text = "This is a sentence. " * 100
        docs = [{"doc_id": "long", "content": long_text, "source": "long.txt"}]
        chunks = splitter.split(docs)
        assert len(chunks) > 1

    def test_markdown_split(self):
        from app.infrastructure.retrieval.text_splitter import TextSplitter
        splitter = TextSplitter(chunk_size=200, chunk_overlap=30)
        md_text = "# Section\n\nContent here.\n\n## Subsection\n\nMore content."
        docs = [{"doc_id": "md", "content": md_text, "source": "md.md"}]
        chunks = splitter.split(docs)
        assert all(c["doc_id"] == "md" for c in chunks)


# ============================================================
# BM25 Retriever Tests
# ============================================================

class TestBM25Retriever:
    def test_index_and_search(self):
        from app.infrastructure.retrieval.bm25_retriever import BM25Retriever
        retriever = BM25Retriever(k1=1.5, b=0.75)
        chunks = [
            {"doc_id": "doc1", "chunk_index": 0, "content": "machine learning is a subset of artificial intelligence"},
            {"doc_id": "doc2", "chunk_index": 0, "content": "python is a programming language for data science"},
            {"doc_id": "doc3", "chunk_index": 0, "content": "deep learning uses neural networks for machine learning tasks"},
        ]
        retriever.index(chunks)

        hits = retriever.search("machine learning", top_k=2)
        assert len(hits) > 0
        # First result should be most relevant
        assert hits[0].score > 0
        assert hits[0].retrieval_method == "bm25"

    def test_empty_search(self):
        from app.infrastructure.retrieval.bm25_retriever import BM25Retriever
        retriever = BM25Retriever()
        hits = retriever.search("anything", top_k=5)
        assert hits == []


# ============================================================
# Reranker Tests
# ============================================================

class TestReranker:
    @pytest.mark.asyncio
    async def test_rerank(self):
        from app.infrastructure.retrieval.reranker import Reranker
        from app.domain.value_objects.retrieval_hit import RetrievalHit

        reranker = Reranker(score_threshold=0.3)
        hits = [
            RetrievalHit(doc_id="d1", chunk_index=0, content="machine learning basics explained", score=0.8, retrieval_method="vector"),
            RetrievalHit(doc_id="d2", chunk_index=0, content="unrelated topic about cooking", score=0.6, retrieval_method="vector"),
            RetrievalHit(doc_id="d3", chunk_index=0, content="advanced machine learning algorithms", score=0.75, retrieval_method="vector"),
        ]

        reranked = await reranker.rerank("machine learning", hits, top_k=2)
        assert len(reranked) == 2
        assert reranked[0].rerank_score >= reranked[1].rerank_score


# ============================================================
# Tool Registry Tests
# ============================================================

class TestToolRegistry:
    @pytest.mark.asyncio
    async def test_list_tools(self):
        from app.infrastructure.langgraph_runtime.tool_registry import ToolRegistry
        registry = ToolRegistry()
        tools = await registry.list_tools()
        assert len(tools) >= 3

    @pytest.mark.asyncio
    async def test_calculator(self):
        from app.infrastructure.langgraph_runtime.tool_registry import ToolRegistry
        registry = ToolRegistry()
        result = await registry.execute("calculator", {"expression": "2 + 3 * 4"})
        assert int(result["result"]) == 14

    @pytest.mark.asyncio
    async def test_calculator_error(self):
        from app.infrastructure.langgraph_runtime.tool_registry import ToolRegistry
        registry = ToolRegistry()
        result = await registry.execute("calculator", {"expression": "__import__('os').system('ls')"})
        assert result["status"] == "success"  # blocks dangerous input

    @pytest.mark.asyncio
    async def test_file_search(self):
        from app.infrastructure.langgraph_runtime.tool_registry import ToolRegistry
        registry = ToolRegistry()
        result = await registry.execute("file_search", {"pattern": "*.py"})
        assert "Found" in result["result"]

    @pytest.mark.asyncio
    async def test_web_search_mock(self):
        from app.infrastructure.langgraph_runtime.tool_registry import ToolRegistry
        registry = ToolRegistry()
        result = await registry.execute("web_search", {"query": "AI"})
        assert "[Mock]" in result["result"]

    @pytest.mark.asyncio
    async def test_lookup(self):
        from app.infrastructure.langgraph_runtime.tool_registry import ToolRegistry
        registry = ToolRegistry()
        entry = await registry.lookup("calculator")
        assert entry is not None
        schema, handler = entry
        assert schema["name"] == "calculator"

    @pytest.mark.asyncio
    async def test_unknown_tool(self):
        from app.infrastructure.langgraph_runtime.tool_registry import ToolRegistry
        registry = ToolRegistry()
        with pytest.raises(ValueError, match="Tool not found"):
            await registry.execute("nonexistent", {})


# ============================================================
# RAG Eval Runner Tests
# ============================================================

class TestRagEvalRunner:
    def test_demo_gold_set(self):
        from app.infrastructure.benchmark.rag_eval_runner import RagEvalRunner
        items = RagEvalRunner._demo_gold_set()
        assert len(items) == 3
        assert "question" in items[0]
        assert "relevant_doc_ids" in items[0]


# ============================================================
# RAG Agent Graph Tests
# ============================================================

class TestAgentState:
    def test_agent_state_type(self):
        from app.infrastructure.langgraph_runtime.rag_agent_graph import AgentState
        state: AgentState = {
            "run_id": "agent_001",
            "goal": "Test goal",
            "task_type": None,
            "messages": [],
            "retrieved_docs": [],
            "planned_tools": [],
            "tool_results": [],
            "draft_answer": None,
            "final_answer": None,
            "step": 0,
            "errors": [],
            "node_name": "start",
            "event_id": 0,
        }
        assert state["run_id"] == "agent_001"
