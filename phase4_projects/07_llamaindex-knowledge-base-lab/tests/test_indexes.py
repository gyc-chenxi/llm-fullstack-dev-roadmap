"""
索引构建单元测试
==================

验证 VectorStoreIndex 和 SummaryIndex 的基本构建和查询功能。
使用 BGE-Small-ZH 轻量模型，device=cpu 避免依赖 GPU。
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from llama_index.core import Settings, VectorStoreIndex, SummaryIndex
from llama_index.core.schema import Document
from llama_index.embeddings.huggingface import HuggingFaceEmbedding


class TestIndexBuilders:
    """索引构建和查询的核心测试。"""

    @pytest.fixture(autouse=True)
    def setup_embed_model(self):
        """注入轻量嵌入模型（避免测试中下载模型，使用 CPU 确保 CI 兼容）。"""
        Settings.embed_model = HuggingFaceEmbedding(
            model_name="BAAI/bge-small-zh-v1.5",
            device="cpu",
        )

    @pytest.fixture
    def sample_docs(self):
        """3 个中文技术文档片段，覆盖核心概念。"""
        return [
            Document(text="Transformer 的核心是 Self-Attention 机制。"),
            Document(text="KV Cache 用于加速自回归生成。"),
            Document(text="RoPE 是一种旋转位置编码方法。"),
        ]

    def test_vector_index_build(self, sample_docs):
        """VectorStoreIndex 能从 Document 列表成功构建。"""
        index = VectorStoreIndex.from_documents(sample_docs)
        assert index is not None

    def test_vector_index_query(self, sample_docs):
        """VectorStoreIndex 基本查询能返回非空结果。"""
        index = VectorStoreIndex.from_documents(sample_docs)
        engine = index.as_query_engine(similarity_top_k=2)
        response = engine.query("什么是 Self-Attention？")
        assert response is not None
        assert len(str(response)) > 0

    def test_summary_index_build(self, sample_docs):
        """SummaryIndex 能从 Document 列表成功构建。"""
        index = SummaryIndex.from_documents(sample_docs)
        assert index is not None

    def test_summary_index_query(self, sample_docs):
        """SummaryIndex tree_summarize 查询能返回非空结果。"""
        index = SummaryIndex.from_documents(sample_docs)
        engine = index.as_query_engine(response_mode="tree_summarize")
        response = engine.query("总结这些内容")
        assert response is not None
        assert len(str(response)) > 0
