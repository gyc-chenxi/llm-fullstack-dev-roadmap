# P8: GraphRAG 知识图谱检索（Day 68-71，4天）

> 核心价值：突破传统 RAG 局限，处理全局/多跳/实体关系问题

---

## 学习目标

- GraphRAG 核心流程：实体抽取 → 关系抽取 → 图谱构建 → 社区检测 → 社区摘要
- Global Search：回答全局性、总结性问题
- Local Search：回答实体关系、多跳问题
- GraphRAG vs Vector RAG：各自的适用场景

## 技术栈

```
graphrag / neo4j (可选) / networkx / llm API
```

## 关键理解

```
Vector RAG: "Transformer 是什么？" → 检索相关文档 → 回答
            ✗ "A 和 B 有什么关系？"（跨文档推理难）

GraphRAG: "A 和 B 有什么关系？" → 图谱中找 A-B 路径 → 回答
          ✗ 图谱构建成本高，不适合超大规模文档
```

## 产出物

- [ ] `graphrag_notes.md` 详细记录
- [ ] 用项目文档构建图谱 → 全局检索 → 局部检索
- [ ] GraphRAG vs Naive RAG 对比报告

## 参考资料

- Microsoft GraphRAG: https://github.com/microsoft/graphrag
- 项目路线详见 `phase4_projects/PROJECTS_SUMMARY.md`
