"""
P8 GraphRAG Lab — Knowledge Graph Retrieval Experimental Platform
====================================================================

完整数据流：

1. 语料构建：
   Wikipedia API + arXiv API → data/raw/*.txt
     ↓ (02_preprocess_docs.py: null-byte strip, CRLF→LF, blank collapse)
   data/input/*.txt

2. GraphRAG 索引管线（DeepSeek LLM + 本地 BGE-M3 Embedding）：
   data/input/ → Text Chunking(1200 words, overlap=100)
     → Entity Extraction(LLM): [{name, type, description}]
     → Relationship Extraction(LLM): [{source, target, description}]
     → Community Detection(Leiden algorithm)
     → Community Reports(LLM): per-community summary
     → Parquet artifacts → data/output/*.parquet

3. Vector RAG 基线（BGE-M3 + ChromaDB）：
   data/input/ → Word Chunking(1200 words, overlap=100) → BGE-M3 Encode(batch=16)
     → ChromaDB PersistentClient → data/vector_store/

4. 对比评估：
   8 条 curated queries → GraphRAG(local/global) + Vector RAG
     → Comparison Report (Markdown) → docs/comparison_report.md

两种 RAG 方法的区别：
  - GraphRAG: 先提取知识图谱(实体+关系+社区)，再基于图结构检索
  - Vector RAG: 直接语义向量检索，不构建中间知识图谱
"""

__version__ = "1.0.0"
