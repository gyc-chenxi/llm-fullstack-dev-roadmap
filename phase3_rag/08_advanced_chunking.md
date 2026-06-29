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

## 7️⃣ 实战案例：文档 Chunking 参数设计与计算

> 以下是一个**完整的具体案例**，从拿到一份真实文档到确定 chunk 参数的全过程。学完这个例子，你可以直接照搬到自己的项目中。

### 📋 场景

你是一家 SaaS 公司的 AI 工程师，需要将一份 **47 页的产品技术白皮书**（约 35,000 字，包含 Markdown 格式的标题、表格、代码块）接入 RAG 知识库。目标是让销售团队能够通过问答快速检索产品技术信息。

**原始文档特征分析**：

| 特征 | 具体数值 | 对 Chunking 的影响 |
|:-----|:---------|:------------------|
| 总字数 | ~35,000 中文字 | 约 35,000 tokens（中文约 1 字 ≈ 1 token）|
| 页数 | 47 页 | 每页约 745 字 |
| 标题层级 | H1×6, H2×24, H3×52 | 语义边界充足，优先文档结构感知 |
| 表格数量 | 8 个 | 需保持表格完整，不能切在表格中间 |
| 代码块 | 12 个 | 代码块必须完整保留 |
| 段落平均长度 | 120 字 | 2-3 个段落组成一个 chunk 比较合理 |

### Step 1：确定 Chunk Size 的理论范围

**约束条件**：

1. **Embedding 模型限制**：使用 `BAAI/bge-small-zh-v1.5`，最大输入 512 tokens
2. **LLM 上下文窗口**：GPT-4o-mini 128K（宽松），但实际使用中每个 query 通常携带 3-5 个 chunks
3. **甜点经验值**：中文 RAG 场景常用 300-600 tokens

**计算有效窗口**：

```
Embedding 模型最大输入: 512 tokens
留余量（约 20%）: 512 × 0.8 ≈ 410 tokens
每个 chunk 保留 50 tokens 用于 metadata（来源、页码、标题）

有效富文本内容上限: 410 - 50 = 360 tokens
中文约 360 字/块
```

### Step 2：确定 Overlap 参数

**Overlap 的作用**：避免关键信息被切在边界导致两边都检索不到。

**计算公式**：

```
Overlap_ideal = max(
    avg_sentence_length × 1.5,       # 至少覆盖 1-2 个完整句子
    chunk_size × overlap_ratio       # 按比例
)
```

**代入数值**：

```
avg_sentence_length = 35 字（中文平均句长）
overlap_ratio = 15%

Overlap_by_sentence: 35 × 1.5 = 52.5 字
Overlap_by_ratio:    360 × 15% = 54 字

取较大值 ≈ 55 字（约 55 tokens）
```

### Step 3：文档结构感知策略（优先于固定大小）

```
文档结构:
┌─ H1: 产品概述 (2,100 字)
│  ├─ H2: 技术架构 (1,200 字)  → 1 chunk (超出360, 需拆分)
│  │  ├─ H3: 前端层 (400 字)    → 1 chunk ✅
│  │  ├─ H3: 后端层 (500 字)    → 需拆分
│  │  └─ H3: 数据层 (100 字)    → 与前一个 H3 合并?
│  └─ H2: 核心特性 (900 字)     → 1 chunk (保留完整)
│
└─ H1: API 参考 (5,000 字)
   ├─ H2: REST API (2,800 字)   → 按 endpoint 再拆分
   └─ H2: WebSocket (2,200 字)  → 按事件类型拆分
```

**决策逻辑**：

```
IF 文档有 H1/H2/H3 标题 THEN
   按标题层级拆分（每个 H2 作为候选 chunk 边界）
   IF 一个 H2 段 > 500 tokens THEN
      按 H3 进一步拆分
   IF 一个 H3 段 < 100 tokens THEN
      与前一个 H3 段合并（同一 H2 下）
   IF 段落包含表格/代码块 THEN
      表格/代码块必须整体保留在一个 chunk 内
      如果表格过大(>500 tokens)，考虑整表拆到多个 chunk 但保证行不跨 chunk
FI
```

### Step 4：最终参数配置

```python
chunk_params = {
    # 主要策略：文档结构感知 + 递归切分作为 fallback
    "primary_strategy": "document_structure_aware",
    "fallback_strategy": "recursive_character",   # 无标题时降级
    
    # 核心参数
    "chunk_size": 360,       # tokens，基于 Embedding 模型 512 limit × 0.8 - metadata
    "chunk_overlap": 55,     # tokens，基于 avg_sentence × 1.5 和 15%
    
    # 文档结构感知配置
    "headers_to_split_on": [
        ("###", "H3"),       # 最小拆分单元
        ("##", "H2"),        # 主要拆分边界
        ("#",  "H1"),        # 保留 H1 作为 metadata
    ],
    
    # 特殊元素保护
    "keep_together": ["table", "code_block"],   # 保持完整
    
    # 边界规则
    "min_chunk_size": 100,   # tokens，小于此值合并到相邻 chunk
    "max_chunk_size": 500,   # tokens，硬上限（超过则二分）
    
    # Metadata 注入
    "metadata_fields": ["source", "page", "h1", "h2", "h3", "chunk_index"],
}
```

### Step 5：结果验证

```python
# 35,000 字文档的实际分块结果
results = {
    "total_chunks": 87,                       # 87 个 chunk
    "avg_chunk_tokens": 342,                  # 接近目标的 360
    "chunks_in_target_range(300-400)": 61,    # 70% 在目标范围内
    "chunks_too_small(<150)": 4,              # 4.6% 太短
    "chunks_too_large(>500)": 3,              # 3.4% 太长
    "tables_broken": 0,                       # 0 个表格被切开 ✅
    "code_blocks_broken": 1,                  # 1 个代码块被切开（过长）
    
    # Overlap 统计
    "avg_overlap_tokens": 52,                 # 接近目标的 55
    "overlap_range": "48-56",                 # 稳定
    
    # 整体空间利用率
    "total_tokens_after_chunking": 29754,     # 含 overlap 的冗余
    "space_waste_pct": 15.0,                  # overlap 导致的冗余
}
```

### Step 6：对比实验

| 策略 | chunk_size | overlap | 检索 Recall@5 | 生成正确率 | 总 tokens |
|:-----|:----------|:--------|:-------------|:----------|:---------|
| 固定大小 | 512 | 0 | 68.3% | 71.2% | 35,000 |
| 固定大小+overlap | 512 | 50 | 72.1% | 74.5% | 40,250 |
| 递归切分 | 400 | 50 | 76.8% | 79.3% | 41,800 |
| **文档结构感知** | **360** | **55** | **82.5%** | **85.1%** | **39,500** |
| Small-to-Big | small=150/big=600 | 30 | **84.2%** | **87.6%** | 48,700 |

**结论**：
- 文档结构感知 + 经过计算的参数相比暴力固定大小，Recall@5 提升了 **14 个百分点**
- Small-to-Big 效果最好但存储翻倍 → 高价值场景优先选择
- **Chunking 不是一次性的工作**——每次迭代后都要用 RAGAS 等工具重新验证

> 💡 **面试加分点**："我在做 Chunking 时不是随便选参数，而是从 Embedding 模型最大输入反向推导有效内容窗口，再根据文档结构分块，最后用对比实验验证——整个过程是可复现、可量化的。"

- [ ] 实现至少 3 种分块策略（固定/语义/递归/Small-to-Big）
- [ ] 跑 chunk_size 对比实验（200/300/500/800/1200），记录 Recall@5
- [ ] 输出一份分块策略对比报告
- [ ] 理解 Late Chunking 概念，能讲清和传统 Chunking 的区别
