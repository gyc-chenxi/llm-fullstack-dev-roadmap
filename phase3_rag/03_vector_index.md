# 🗂️ 03 — 向量索引：FAISS 三种索引 + Chroma 实战

> 🎯 **目标**：掌握 Flat / IVFFlat / HNSW 三种索引的适用场景，能用 Chroma 管理向量元数据。
> ⏱️ 预计时间：2 天

---

## 📋 三种索引快速对比

| 索引 | 原理 | 速度 | 召回率 | 适用规模 | 构建时间 |
|------|------|------|--------|---------|----------|
| **IndexFlatIP** | 暴力搜索 | 慢 | 100% | < 10万 | 即时 |
| **IndexIVFFlat** | 聚类 + 搜最近N个聚类 | 快 10-50x | ~95% | 10万-1000万 | 需训练 |
| **IndexHNSW** | 分层图搜索 | 最快 | ~98% | 百万-亿级 | 需建图 |

---

## 1️⃣ IndexFlatIP：暴力搜索基准

```python
import faiss, numpy as np

# 设已有 10000 条 512 维归一化 embedding
dim = 512
embeddings = np.random.randn(10000, dim).astype('float32')
faiss.normalize_L2(embeddings)  # 归一化 → 内积 = 余弦

index_flat = faiss.IndexFlatIP(dim)
index_flat.add(embeddings)

# 检索
query = np.random.randn(1, dim).astype('float32')
faiss.normalize_L2(query)
scores, ids = index_flat.search(query, k=5)
```

---

## 2️⃣ IndexIVFFlat：聚类加速

```python
nlist = 100  # 聚类中心数（经验: sqrt(N) ~ 4*sqrt(N)）

# Step 1: 创建量化器（用 Flat 索引聚类中心）
quantizer = faiss.IndexFlatIP(dim)

# Step 2: 创建 IVFFlat
index_ivf = faiss.IndexIVFFlat(quantizer, dim, nlist, faiss.METRIC_INNER_PRODUCT)

# Step 3: 🔑 必须先训练！用聚类算法建 nlist 个聚类中心
index_ivf.train(embeddings)  # 耗时：10000 条 ~1-2 秒
index_ivf.add(embeddings)

# Step 4: 检索时只搜最近的 nprobe 个聚类
index_ivf.nprobe = 10  # 搜 10 个聚类（越大召回越高、越慢）
scores, ids = index_ivf.search(query, k=5)
```

### 📌 nlist 和 nprobe 调优

| nlist | 聚类数 | 每聚类向量数 | 搜索速度 | 召回率 |
|-------|--------|-----------|---------|--------|
| 50 | 少 | 多 (~200) | 慢 | 高 |
| 100 | 中 | 中 (~100) | 中 | 中 |
| 200 | 多 | 少 (~50) | 快 | 低 |

> nprobe=10 通常能保留 95%+ 召回率，速度比 Flat 快 10-20x。

---

## 3️⃣ IndexHNSW：图搜索最快

```python
# HNSW 参数
M = 32              # 每个节点的最大连接数（越大召回越高、内存越大）
efConstruction = 200  # 建图时的搜索深度
efSearch = 64        # 检索时的搜索深度

index_hnsw = faiss.IndexHNSWFlat(dim, M)
index_hnsw.hnsw.efConstruction = efConstruction
index_hnsw.hnsw.efSearch = efSearch
index_hnsw.add(embeddings)  # 不需要 train()

scores, ids = index_hnsw.search(query, k=5)
```

### 📌 HNSW 参数指南

| 参数 | 含义 | 建议值 | 调大效果 |
|------|------|--------|----------|
| **M** | 节点连接数 | 16-64 | 召回↑ 但内存↑ 建图慢 |
| **efConstruction** | 建图搜索深度 | 100-500 | 图质量↑ 但建图慢 |
| **efSearch** | 检索搜索深度 | 16-256 | 召回↑ 但检索慢 |

---

## 4️⃣ 三种索引性能 Benchmark

```python
import time

N, dim = 10000, 512
emb = np.random.randn(N, dim).astype('float32')
faiss.normalize_L2(emb)

# 基准 embedding
gt_index = faiss.IndexFlatIP(dim)
gt_index.add(emb)

queries = np.random.randn(100, dim).astype('float32')
faiss.normalize_L2(queries)

# Ground truth（100% 召回）
_, gt_ids = gt_index.search(queries, k=5)

indexes = {
    'Flat':   faiss.IndexFlatIP(dim),
    'IVFFlat': faiss.IndexIVFFlat(faiss.IndexFlatIP(dim), dim, 100),
    'HNSW':   faiss.IndexHNSWFlat(dim, 32),
}

for name, idx in indexes.items():
    t0 = time.time()
    if name == 'IVFFlat':
        idx.train(emb)
    idx.add(emb)
    build_time = time.time() - t0

    if name == 'IVFFlat':
        idx.nprobe = 10
    if name == 'HNSW':
        idx.hnsw.efSearch = 64

    t0 = time.time()
    _, search_ids = idx.search(queries, k=5)
    search_time = (time.time() - t0) / 100 * 1000

    # 召回率
    recall = sum(
        len(set(gt_ids[i]) & set(search_ids[i])) / 5
        for i in range(100)
    ) / 100

    print(f"{name:<10} build={build_time:.2f}s  search={search_time:.1f}ms/q  recall={recall:.1%}")
```

**预期输出**：
```
Flat       build=0.01s  search=0.8ms/q  recall=100.0%
IVFFlat    build=1.20s  search=0.04ms/q recall=95.3%
HNSW       build=3.50s  search=0.02ms/q recall=98.7%
```

---

## 5️⃣ Chroma 进阶用法

```python
import chromadb

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(
    name="phase2_notes",
    metadata={"hnsw:space": "cosine"},  # 余弦相似度
)

# 添加文档（含 metadata）
collection.add(
    documents=[c['content'] for c in chunks],
    metadatas=[c['metadata'] for c in chunks],
    ids=[f"chunk_{i}" for i in range(len(chunks))],
)

# 带 metadata 过滤的检索
results = collection.query(
    query_texts=["什么是 RoPE？"],
    n_results=5,
    where={"format": "markdown"},   # 🔑 只搜 Markdown 文件
    # where={"page": {"$gte": 2}},  # 只搜第 2 页及以后
)
print(f"检索到 {len(results['documents'][0])} 条")
print(f"Meta: {results['metadatas'][0]}")

# Collection 管理
print(client.list_collections())
# collection.delete()  # 删除整个 collection
```

---

## 6️⃣ 增量更新策略

```python
# FAISS: IDMap 包装
base_index = faiss.IndexFlatIP(dim)
index_with_ids = faiss.IndexIDMap(base_index)
index_with_ids.add_with_ids(new_embeddings, new_ids)  # ids 必须是 int64

# Chroma: 直接用 add
collection.add(
    documents=["新文档内容"],
    metadatas=[{"source": "new_file.md"}],
    ids=["chunk_new_001"],
)
# Chroma 自动更新内部索引

# 删除：Chroma 原生的
collection.delete(ids=["chunk_old_001"])
```

---

## 7️⃣ Embedding 缓存策略

```python
import pickle, hashlib, os

CACHE_DIR = "./embedding_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

def get_cache_path(docs: list[dict]) -> str:
    """用文档列表的 hash 作为缓存 key"""
    content_hash = hashlib.md5(
        ''.join(d['content'][:100] for d in docs).encode()
    ).hexdigest()
    return f"{CACHE_DIR}/{content_hash}.pkl"

def encode_with_cache(model, chunk_texts, docs):
    cache_path = get_cache_path(docs)
    if os.path.exists(cache_path):
        print(f"✅ 加载缓存: {cache_path}")
        with open(cache_path, 'rb') as f:
            return pickle.load(f)

    print("🧮 编码中...")
    embeddings = model.encode(chunk_texts, normalize_embeddings=True)
    with open(cache_path, 'wb') as f:
        pickle.dump(embeddings, f)
    return embeddings
```

---

## 8️⃣ 选型决策树

```
你的数据规模？
  ├── < 1万 → Chroma（最简单，metadata 过滤方便）
  ├── 1万-100万 → FAISS IndexIVFFlat（需要训练，速度够用）
  └── > 100万 → FAISS IndexHNSW（最快，内存大）

你需要 metadata 过滤吗？
  ├── 是（按来源/日期/格式过滤） → Chroma 或 Milvus
  └── 否 → FAISS（纯向量检索最快）

你需要分布式/多用户吗？
  ├── 是 → Milvus / Qdrant
  └── 否 → FAISS / Chroma（单机够用）
```

---

## 🚨 翻车现场

| 现象 | 原因 | 解决 |
|------|------|------|
| IVFFlat 检索全是 NaN | 忘了 `train()` | 必须先 `index.train(embeddings)` |
| HNSW 建图 OOM | M 太大 | M=16-32 足够，64 是极限 |
| Chroma 检索结果为空 | metadata where 条件太严格 | 先不加 where 确认有数据 |
| 缓存读取出错 | 文档变了但 hash 没变 | hash 用更多特征（文件名+大小） |
| FAISS 持久化后加载失败 | 版本不兼容 | 记录 FAISS 版本，必要时重建索引 |

---

## ✅ 产出物 Checklist

- [ ] 跑通 Flat / IVFFlat / HNSW 三种索引
- [ ] 用 10000 条向量做 benchmark，对比速度和召回率
- [ ] 用 Chroma 做 metadata 过滤检索
- [ ] 实现 embedding 缓存，避免重复编码
- [ ] 了解 IVFFlat 的 nlist/nprobe 和 HNSW 的 M/efSearch 参数
