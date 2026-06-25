"""
摄取管道单元测试
==================

验证 IngestionPipeline 创建和缓存哈希的确定性。
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from llama_index.core.schema import Document

from src.ingestion.pipeline import build_ingestion_pipeline, _compute_docs_hash
from src.utils.config import Config


class TestIngestionPipeline:
    """摄取管道的核心逻辑测试。"""

    @pytest.fixture
    def config(self):
        return Config.load("configs/settings.yaml")

    @pytest.fixture
    def sample_docs(self):
        return [
            Document(text="Transformer 是一种基于注意力机制的神经网络架构。"),
            Document(text="LoRA 通过低秩分解实现参数高效微调。"),
        ]

    def test_pipeline_creation(self, config):
        """管道创建不报错，至少包含 2 个转换器。"""
        pipeline = build_ingestion_pipeline(config)
        assert pipeline is not None
        assert len(pipeline.transformations) >= 2

    def test_docs_hash_deterministic(self, sample_docs):
        """相同文档应生成相同 hash（确定性）。"""
        h1 = _compute_docs_hash(sample_docs)
        h2 = _compute_docs_hash(sample_docs)
        assert h1 == h2

    def test_docs_hash_changes_with_content(self, sample_docs):
        """内容变化应导致 hash 改变（避免缓存过期不更新）。"""
        h1 = _compute_docs_hash(sample_docs)
        sample_docs[0].text = "不同的内容"
        h2 = _compute_docs_hash(sample_docs)
        assert h1 != h2
