# ✂️ 08 — 高级分块策略

> 🎯 **目标**：掌握 5 种分块策略，理解 Small-to-Big 和多粒度索引对 RAG 效果的提升。
> ⏱️ 预计时间：1 天

---

## 📋 为什么分块策略是 RAG 的第一道坎？

| 分块太大 | 分块太小 |
|---------|---------|
| 检索噪声多 | 丢失上下文 |
| 一次 chunk 包含多个主题 | 关键信息被切断 |
| LLM 上下文浪费在无关内容上 | 相邻 chunk 信息重复 |

---

## 1️⃣ Small-to-Big 检索

```
索引阶段：用小 chunk（200 tokens）建索引 → 检索精度高
生成阶段：把小 chunk 对应的"父 chunk"（800 tokens）送给 LLM → 上下文完整

实现：每个 chunk 存储时附 parent_chunk_id
```

```python
def small_to_big_chunk(text, small_size=200, big_size=800):
    big_chunks = chunk_fixed(text, big_size, 100)
    result = []
    for big_id, big in enumerate(big_chunks):
        smalls = chunk_fixed(big, small_size, 50)
        for s in smalls:
            result.append({'content': s, 'parent_content': big, 'parent_id': big_id})
    return result
```

## 2️⃣ 多粒度索引

同时维护三层索引：文档级（摘要）→ 段落级（500 字）→ 句子级（100 字）。检索时先搜句子级，命中的句子所属段落作为上下文送 LLM。

## 3️⃣ Late Chunking 概念

传统：先分块 → 再 Embedding。Late Chunking：先整篇文档 Embedding（token-level） → 再按 chunk 边界 pooling。优势是 token embedding 包含全局上下文。

## 4️⃣ Chunk Size 对比实验

| chunk_size | 平均检索精度 | 答案完整度 | Token 消耗 |
|-----------|------------|-----------|-----------|
| 200 | 0.85 | 0.62 | 低 |
| 500 | 0.78 | 0.85 | 中 |
| 1000 | 0.65 | 0.92 | 高 |

> 🔥 建议：索引用小 chunk (200-300)，生成用大 context。

---

## ✅ 产出物 Checklist
- [ ] 实现 Small-to-Big 检索
- [ ] 对比不同 chunk_size 的检索效果
