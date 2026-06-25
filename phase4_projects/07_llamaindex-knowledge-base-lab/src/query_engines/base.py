"""
查询引擎基类
===============

定义统一的查询接口抽象和来源格式化工具。

子类实现层次：
  BaseQueryEngine (ABC)
    ├── VectorQueryEngine (VectorStoreIndex.as_query_engine)
    ├── SummaryQueryEngine (SummaryIndex.as_query_engine)
    └── RouterQueryEngine (LLMSingleSelector 多知识库路由)
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from llama_index.core.schema import NodeWithScore


class BaseQueryEngine(ABC):
    """查询引擎抽象基类。"""

    @abstractmethod
    def query(self, question: str) -> str:
        """执行查询并返回回答文本。"""
        ...

    def query_with_sources(self, question: str) -> dict:
        """查询并附带来源信息。"""
        raise NotImplementedError


def format_sources(source_nodes: List[NodeWithScore]) -> str:
    """格式化检索来源为可读文本。

    输出格式：
      📎 引用来源:
        [1] [0.95] file_name.md | text preview...
        [2] [0.87] file_name.pdf | text preview...
    """
    lines = ["\n📎 引用来源:"]
    for i, node in enumerate(source_nodes, 1):
        score = node.score or 0.0
        file_name = node.metadata.get("file_name", "unknown")
        preview = node.text[:60].replace("\n", " ")
        lines.append(f"  [{i}] [{score:.2f}] {file_name} | {preview}...")
    return "\n".join(lines)
