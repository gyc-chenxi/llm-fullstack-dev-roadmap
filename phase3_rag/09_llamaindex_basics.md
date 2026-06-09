# 🦙 09 — LlamaIndex 入门

> 🎯 **目标**：掌握 LlamaIndex 的核心抽象，对比 LangChain RAG 方案。
> ⏱️ 预计时间：1 天

---

## 📋 LlamaIndex vs LangChain

| 维度 | LlamaIndex | LangChain |
|------|-----------|-----------|
| 核心定位 | 数据→LLM 的桥梁 | 通用 LLM 应用框架 |
| RAG 能力 | ⭐⭐⭐⭐⭐ 原生最强 | ⭐⭐⭐ 需组装 |
| Agent 能力 | ⭐⭐ | ⭐⭐⭐⭐ LangGraph |
| 学习曲线 | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| 适合 | 知识库/文档问答 | 复杂 Agent 工作流 |

---

## 1️⃣ IngestionPipeline 文档摄取

```python
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

pipeline = IngestionPipeline(
    transformations=[
        SentenceSplitter(chunk_size=500, chunk_overlap=50),
        HuggingFaceEmbedding(model_name="BAAI/bge-small-zh-v1.5"),
    ],
)
nodes = pipeline.run(documents=docs)
```

## 2️⃣ QueryEngine 问答

```python
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

docs = SimpleDirectoryReader("./phase2_notes").load_data()
index = VectorStoreIndex.from_documents(docs)
engine = index.as_query_engine(similarity_top_k=5, streaming=True)
response = engine.query("什么是 KV Cache？")
print(response)
```

## 3️⃣ RouterQueryEngine 多知识库路由

```python
from llama_index.core.tools import QueryEngineTool, RouterQueryEngine

tool1 = QueryEngineTool.from_defaults(engine_phase2, description="Phase 2 学习笔记")
tool2 = QueryEngineTool.from_defaults(engine_paper, description="学术论文")
router = RouterQueryEngine.from_defaults([tool1, tool2])
# 自动根据问题内容选择知识库
```

## 4️⃣ SubQuestionQueryEngine 复杂问题拆解

```python
from llama_index.core.query_engine import SubQuestionQueryEngine
engine = SubQuestionQueryEngine.from_defaults([tool1, tool2])
# 自动把 "对比 Phase 2 和论文 X 的 Attention 机制" 拆成两个子问题
```

---

## ✅ 产出物 Checklist
- [ ] 用 LlamaIndex 重写 Phase 2 笔记问答
- [ ] 对比 LangChain 和 LlamaIndex 的代码量
- [ ] 尝试 RouterQueryEngine 多知识库路由
