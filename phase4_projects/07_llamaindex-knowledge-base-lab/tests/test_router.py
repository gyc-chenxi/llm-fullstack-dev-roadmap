"""
多知识库路由单元测试
=======================

验证 RouterQueryEngine 的创建和路由元数据正确性。
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from llama_index.core import Settings, VectorStoreIndex
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core.query_engine import RouterQueryEngine
from llama_index.core.selectors import LLMSingleSelector
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.schema import Document


class TestRouter:
    """RouterQueryEngine 的路由逻辑测试。"""

    @pytest.fixture(autouse=True)
    def setup(self):
        Settings.embed_model = HuggingFaceEmbedding(
            model_name="BAAI/bge-small-zh-v1.5",
            device="cpu",
        )

    def test_router_creation(self):
        """路由器能带 2 个知识库工具创建成功。"""
        tool_a = QueryEngineTool(
            query_engine=VectorStoreIndex.from_documents(
                [Document(text="内容 A")]
            ).as_query_engine(),
            metadata=ToolMetadata(
                name="tool_a",
                description="包含 Transformer 和 Attention 的学习笔记",
            ),
        )
        tool_b = QueryEngineTool(
            query_engine=VectorStoreIndex.from_documents(
                [Document(text="内容 B")]
            ).as_query_engine(),
            metadata=ToolMetadata(
                name="tool_b",
                description="包含 LoRA 和 DPO 的学术论文",
            ),
        )

        router = RouterQueryEngine(
            selector=LLMSingleSelector.from_defaults(),
            query_engine_tools=[tool_a, tool_b],
        )
        assert router is not None
        assert len(router._metadatas) == 2
