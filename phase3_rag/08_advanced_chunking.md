# ✂️ 08 — 高级分块策略

> 🎯 **目标**：掌握 5 种分块策略，理解 Small-to-Big 和多粒度索引对 RAG 效果的提升。
> ⏱️ 预计时间：1 天

---

## 📋 为什么分块策略是 RAG 的第一道坎？

分块质量直接决定检索质量。分块太大→噪声多；分块太小→上下文断裂。

| 分块太大 (1000+) | 分块太小 (<100) | 甜点 (300-500) |
|:----------------|:---------------|:--------------|
| 一个 chunk 包含多个主题 | 关键信息被切断 | 语义完整 + 定位准确 |
| LLM 上下文浪费在无关内容 | 相邻 chunk 信息高度重复 | Chunk 间有一定独立性 |
| 检索 precision 低（~0.65） | 检索 recall 低（~0.55） | 综合最优（precision ~0.78） |

---

## 1️⃣ 五种分块策略对比

| 策略 | 做法 | 优点 | 缺点 | 适用 |
|:-----|:----|:-----|:-----|:----|
| **固定大小** | 每 N 字符切一刀 | 简单快速 | 可能在句子中间切断 | 通用 baseline |
| **递归切分** | 先按 `\n\n`，不够再按 `\n`，再按空格 | 尽可能保持语义边界 | 不能保证完全不分词 | LangChain 默认 |
| **语义切分** | 按句子边界 + 最小/最大长度约束 | 语义最完整 | 需要 NLP 模型 | 需要高质量 chunk |
| **文档结构感知** | Markdown 按 ## 标题，PDF 按段落 | 利用文档原有结构 | 依赖文档格式 | 技术文档/RFP |
| **Small-to-Big** | 小 chunk 索引 + 父 chunk 送 LLM | 检索精度 + 上下文完整 | 存储加倍 | 🔥 推荐 |

---

## 2️⃣ 完整实现

### 固定大小 + Overlap

```python
def chunk_fixed(text: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
    """最基础的固定大小分块"""
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start = end - overlap
    return chunks
```

### 递归切分（LangChain 同款思路）

```python
def chunk_recursive(text: str, chunk_size: int = 500, 
                    separators: list[str] = None) -> list[str]:
    """递归按分隔符优先级切分"""
    if separators is None:
        separators = ["\n\n", "\n", "。", ".", " ", ""]
    
    if len(text) <= chunk_size:
        return [text] if text.strip() else []
    
    for sep in separators:
        if sep == "":
            # 最后手段：硬切
            return chunk_fixed(text, chunk_size, 100)
        if sep in text:
            parts = text.split(sep)
            chunks = []
            current = ""
            for part in parts:
                if len(current) + len(part) + len(sep) <= chunk_size:
                    current += (sep if current else "") + part
                else:
                    if current: chunks.append(current)
                    current = part
            if current: chunks.append(current)
            return chunks
    return [text]
```

### 语义切分（句子边界）

```python
import re

def chunk_semantic(text: str, min_chunk: int = 200, 
                   max_chunk: int = 600) -> list[str]:
    """按句子边界切分，保证语义完整"""
    # 中英文句子分割
    sentences = re.split(r'(?<=[。！？.!?\n])', text)
    
    chunks = []
    current = ""
    for sent in sentences:
        if not sent.strip(): continue
        
        if len(current) + len(sent) <= max_chunk:
            current += sent
        else:
            if len(current) >= min_chunk:
                chunks.append(current)
                current = sent
            else:
                # 当前 chunk 太短，强行合并
                current += sent
    if current.strip():
        chunks.append(current)
    return chunks
```

### Small-to-Big 检索

```python
def small_to_big_chunk(text: str, small_size: int = 300, 
                       big_size: int = 1000, overlap: int = 50) -> list[dict]:
    """
    小 chunk 建索引（检索精度高）
    大 chunk 送 LLM（上下文完整）
    返回: [{'content': 小chunk, 'parent_content': 所属大chunk, 'parent_id': 索引}]
    """
    big_chunks = chunk_fixed(text, big_size, overlap)
    result = []
    for big_id, big_chunk in enumerate(big_chunks):
        smalls = chunk_fixed(big_chunk, small_size, overlap // 2)
        for small in smalls:
            result.append({
                'content': small,
                'parent_content': big_chunk,
                'parent_id': big_id,
            })
    return result

# 检索时：用 content 匹配，返回 parent_content
# 索引时：只对 content 做 embedding
# 生成时：拼接 parent_content（去重）送给 LLM
```

---

## 3️⃣ 多粒度索引

同时维护三层索引，检索时逐级定位：

```
文档级索引 → 段落级索引 → 句子级索引

检索流程：
  query → 先查句子级（精确定位）
       → 命中句子所属段落作为上下文
       → 若命中太少 → fallback 到段落级
       → 若还不够 → fallback 到文档级摘要
```

```python
class MultiGranularIndex:
    def __init__(self):
        self.doc_index = {}    # 文档级：每篇文档的摘要
        self.para_index = {}   # 段落级：500字段落
        self.sent_index = {}   # 句子级：100字句子
    
    def build(self, documents: list[dict]):
        for doc in documents:
            # 文档级
            summary = self._summarize(doc['content'])
            self.doc_index[doc['id']] = summary
            
            # 段落级 + 句子级
            paras = chunk_fixed(doc['content'], 500, 50)
            for p_id, para in enumerate(paras):
                para_key = f"{doc['id']}_p{p_id}"
                self.para_index[para_key] = para
                
                sents = chunk_semantic(para, 50, 150)
                for s_id, sent in enumerate(sents):
                    sent_key = f"{para_key}_s{s_id}"
                    self.sent_index[sent_key] = {
                        'content': sent, 'para_key': para_key
                    }
    
    def search(self, query: str, top_k: int = 5) -> list[str]:
        # 1. 句子级检索
        sent_results = vector_search(query, list(self.sent_index.values()), top_k)
        # 2. 向上查段落
        para_keys = set()
        for sent in sent_results:
            para_keys.add(sent['para_key'])
        # 3. 返回不重复的段落
        return [self.para_index[k] for k in para_keys][:top_k]
```

---

## 4️⃣ Late Chunking 概念

传统 Chunking：先分块 → 再 Embedding。每个 chunk 的 embedding 独立计算，丢失跨 chunk 的全局上下文。

Late Chunking：先用整篇文档做 token-level embedding → 再按 chunk 边界对 token embeddings 做 pooling。

```
传统:   [chunk1]→emb1  [chunk2]→emb2  [chunk3]→emb3
         ↑ 互相独立，全局信息丢失

Late:   全文→[tok1][tok2][tok3][tok4][tok5][tok6]→token embeddings
              ↓      ↓      ↓
            pool1  pool2  pool3  每个 chunk embedding 包含全局上下文
```

> Late Chunking 目前需要特定 embedding 模型支持（如 jina-embeddings-v3），大部分开源模型暂不支持。但这是一个重要方向。

---

## 5️⃣ Chunk Size 对比实验

```python
from sentence_transformers import SentenceTransformer
import numpy as np

def benchmark_chunk_sizes(texts: list[str], queries: list[str], 
                          sizes: list[int] = [200, 300, 500, 800, 1200]):
    """对比不同 chunk_size 的检索效果"""
    model = SentenceTransformer("BAAI/bge-small-zh-v1.5")
    
    for size in sizes:
        all_chunks, chunk_to_doc = [], []
        for doc_id, text in enumerate(texts):
            chunks = chunk_fixed(text, size, size // 5)
            all_chunks.extend(chunks)
            chunk_to_doc.extend([doc_id] * len(chunks))
        
        embeddings = model.encode(all_chunks, normalize_embeddings=True)
        query_embs = model.encode(queries, normalize_embeddings=True)
        
        # 计算 Recall@5
        recall_hits = 0
        for q_emb, q_text in zip(query_embs, queries):
            scores = np.dot(embeddings, q_emb)
            top5 = np.argsort(scores)[-5:][::-1]
            # 判断 top5 中是否包含相关文档
            relevant_docs = set(...)
            if any(chunk_to_doc[i] in relevant_docs for i in top5):
                recall_hits += 1
        
        print(f"chunk_size={size:4d} | Recall@5={recall_hits/len(queries):.2%}")

# 输出示例：
# chunk_size= 200 | Recall@5=72.5%
# chunk_size= 300 | Recall@5=78.3%  ← 推荐
# chunk_size= 500 | Recall@5=76.1%
# chunk_size= 800 | Recall@5=68.4%
# chunk_size=1200 | Recall@5=58.2%
```

---

## 6️⃣ 选型建议

| 场景 | 推荐策略 | chunk_size |
|:-----|:--------|:---------|
| 通用知识库 | 递归切分 + Overlap | 400-600 |
| 技术文档(Markdown) | 文档结构感知（按 ## 标题） | — |
| 法律/合同 | Small-to-Big（小索引用大上下文） | 300/1000 |
| 多主题长文档 | 语义切分 + 多粒度索引 | 200-500 |
| 快速原型 | 固定大小 | 500 |

> 🔥 **面试金句**："我不是简单地固定大小切分——会根据文档类型选分块策略。技术文档用标题拆分，长文档用 Small-to-Big，还在做多粒度索引的对比实验。"

---

## ✅ 产出物 Checklist

- [ ] 实现至少 3 种分块策略（固定/语义/递归/Small-to-Big）
- [ ] 跑 chunk_size 对比实验（200/300/500/800/1200），记录 Recall@5
- [ ] 输出一份分块策略对比报告
- [ ] 理解 Late Chunking 概念，能讲清和传统 Chunking 的区别
