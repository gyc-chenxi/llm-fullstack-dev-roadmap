# P6: LangGraph 企业级 RAG（Day 61-64，4天）

> 核心价值：构建可观测、可恢复、可评测的 RAG 状态机

---

## 学习目标

- LangChain Retriever、Tool、Memory、LCEL
- LangGraph StateGraph、条件边、循环、Checkpoint
- 完整 RAG Agent 状态机（详见 `phase3_rag/langgraph_rag/`）
- SSE 事件流推送每个阶段的进度
- Trace 日志记录（每次检索、生成、验证都可回溯）

## 技术栈

```
langchain / langgraph / fastapi / sse-starlette
```

## 产出物

- [ ] `langgraph_rag_app/` 完整应用
- [ ] Trace 日志示例
- [ ] 失败恢复演示（检索不够好 → 重写查询 → 重新检索）

## 参考资料

- LangGraph 官方文档
- 本仓库 `phase3_rag/langgraph_rag/README.md` 有完整实现指南
