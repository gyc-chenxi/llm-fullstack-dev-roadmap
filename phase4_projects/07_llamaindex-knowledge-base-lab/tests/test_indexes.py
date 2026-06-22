"""索引构建单元测试."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from llama_index.core import Settings, VectorStoreIndex, SummaryIndex
from llama_index.core.schema import Document
from llama_index.embeddings.huggingface import HuggingFaceEmbedding


class TestIndexBuilders:
    """测试索引构建逻辑。"""

    @pytest.fixture(autouse=True)
    def setup_embed_model(self):
        """注入轻量嵌入模型（避免测试中下载模型）。"""
        Settings.embed_model = HuggingFaceEmbedding(
            model_name="BAAI/bge-small-zh-v1.5",
            device="cpu",
        )

    @pytest.fixture
    def sample_docs(self):
        return [
            Document(text="Transformer 的核心是 Self-Attention 机制。"),
            Document(text="KV Cache 用于加速自回归生成。"),
            Document(text="RoPE 是一种旋转位置编码方法。"),
        ]

    def test_vector_index_build(self, sample_docs):
        """测试 VectorStoreIndex 构建成功。"""
        index = VectorStoreIndex.from_documents(sample_docs)
        assert index is not None

    def test_vector_index_query(self, sample_docs):
        """测试 VectorStoreIndex 基本查询。"""
        index = VectorStoreIndex.from_documents(sample_docs)
        engine = index.as_query_engine(similarity_top_k=2)
        response = engine.query("什么是 Self-Attention？")
        assert response is not None
        assert len(str(response)) > 0

    def test_summary_index_build(self, sample_docs):
        """测试 SummaryIndex 构建成功。"""
        index = SummaryIndex.from_documents(sample_docs)
        assert index is not None

    def test_summary_index_query(self, sample_docs):
        """测试 SummaryIndex 总结查询。"""
        index = SummaryIndex.from_documents(sample_docs)
        engine = index.as_query_engine(response_mode="tree_summarize")
        response = engine.query("总结这些内容")
        assert response is not None
        assert len(str(response)) > 0
