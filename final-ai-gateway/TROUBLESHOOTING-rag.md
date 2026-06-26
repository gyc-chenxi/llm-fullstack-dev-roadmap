# Troubleshooting: RAG 检索质量问题

## 症状

```
RAG 答案不相关 / 检索结果为空 / Citation 校验失败
```
或
```
RagQualityGuard: low retrieval score
RagQualityGuard: no citations provided
```

## 原因

1. 文档未正确加载或分割
2. Embedding 模型问题
3. 检索参数配置不当
4. Reranker 阈值过高
5. Citation 策略配置过于严格

## 解决步骤

### 1. 检查文档加载

```python
from app.infrastructure.retrieval.document_loader import DocumentLoader
from app.infrastructure.retrieval.text_splitter import TextSplitter

import asyncio

async def test():
    loader = DocumentLoader(base_dir="./docs")
    docs = await loader.load("sample.md")
    print(f"Loaded {len(docs)} documents")

    splitter = TextSplitter(chunk_size=512, chunk_overlap=50)
    chunks = splitter.split(docs)
    print(f"Split into {len(chunks)} chunks")

    for i, chunk in enumerate(chunks[:3]):
        print(f"Chunk {i}: {chunk['content'][:100]}...")

asyncio.run(test())
```

### 2. 检查向量存储

```python
from app.infrastructure.retrieval.vector_store_repo import VectorStoreRepo

async def test():
    store = VectorStoreRepo()
    await store.initialize()
    count = await store.count()
    print(f"Vector store has {count} documents")

asyncio.run(test())
```

### 3. 调试检索结果

```python
from app.infrastructure.retrieval.bm25_retriever import BM25Retriever
from app.infrastructure.retrieval.reranker import Reranker

# 测试 BM25
bm25 = BM25Retriever()
chunks = [{"doc_id": "test", "chunk_index": 0, "content": "..."}]
bm25.index(chunks)
hits = bm25.search("your query", top_k=5)
for h in hits:
    print(f"BM25: {h.doc_id} score={h.score:.3f}")

# 测试 Reranker
reranker = Reranker(score_threshold=0.3)
reranked = await reranker.rerank("your query", hits, top_k=3)
for h in reranked:
    print(f"Rerank: {h.doc_id} score={h.rerank_score:.3f}")
```

### 4. 调整参数

在 `configs/rag.yaml` 中调整：

```yaml
retrieval:
  default_top_k: 10      # 增大检索数量
  rerank_top_k: 5        # 增大重排保留数
  min_retrieval_score: 0.1  # 降低阈值（允许更多结果）
  min_rerank_score: 0.3

reranker:
  score_threshold: 0.3   # 降低重排阈值

citation:
  require: true
  min_citations: 1
  min_relevance_score: 0.2  # 降低引用相关性阈值
```

### 5. 检查 Embedding 模型

```bash
# 确认 sentence-transformers 可用
python -c "from sentence_transformers import SentenceTransformer; print('OK')"

# 如果没有安装
pip install sentence-transformers

# ChromaDB 需要
pip install chromadb
```

### 6. 检查 RAG Quality Guard

`RagQualityGuard` 有三层检查：
1. **检索质量**：平均 retrieval score < 0.3 → 拒绝
2. **重排质量**：平均 rerank score < 0.5 → 拒绝
3. **引用校验**：citation 中的 doc_id 必须在 retrieved_docs 中

暂时关闭 quality guard 进行调试：
```python
guard = RagQualityGuard(
    min_retrieval_score=0.0,
    min_rerank_score=0.0,
    require_citations=False,
)
```

## 预防措施

- 确保文档已正确加载并入库
- 定期运行 `make eval-rag` 监控检索质量
- 调整 chunk_size 和 overlap 适应文档类型
- 对于中文文档，使用中文 embedding 模型
