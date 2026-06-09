# 🏭 05 — 开源 Agent 平台实战：Dify / RAGFlow / Coze

> 🎯 **目标**：掌握 Dify/RAGFlow/Coze 三个主流平台的部署与使用，知道什么时候用平台、什么时候自建。
> ⏱️ 预计时间：2 天

---

## 📋 三平台对比

| 维度 | Dify | RAGFlow | Coze（扣子） |
|------|------|---------|-------------|
| 定位 | 可视化 LLM 应用 | 深度文档理解 RAG | Agent 搭建平台 |
| 开源 | ✅ Apache 2.0 | ✅ Apache 2.0 | ❌ 字节跳动 SaaS |
| RAG 能力 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Agent 能力 | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| 部署难度 | ⭐⭐ Docker 一键 | ⭐⭐ Docker 一键 | ⭐ 无需部署 |
| 适合场景 | 企业知识库+工作流 | 复杂文档解析 RAG | 快速验证 Bot 想法 |

---

## 1️⃣ Dify 实战

```bash
# Docker 部署
git clone https://github.com/langgenius/dify.git
cd dify/docker
docker compose up -d  # → http://localhost:3000
```

### 知识库问答 Agent 搭建流程
```
1. 创建知识库 → 上传 Markdown/PDF 文档
2. 创建应用 → 选择 "Chatbot" 模板
3. 关联知识库 + 配置 LLM（OpenAI/DeepSeek）
4. 编排 Chatflow：开始→知识检索→LLM→回答
5. 发布 + API 调用
```

### Dify API 调用
```python
resp = requests.post('https://your-dify/v1/chat-messages',
    headers={'Authorization': 'Bearer app-xxx'},
    json={'query': '什么是 RAG？', 'user': 'user-001', 'response_mode': 'streaming'})
```

---

## 2️⃣ RAGFlow 实战

```bash
git clone https://github.com/infiniflow/ragflow.git
cd ragflow/docker
docker compose up -d  # → http://localhost:80
```

### RAGFlow 特色
- 深度文档解析：PDF 表格提取、扫描件 OCR、复杂排版识别
- Chunk 策略：知识图谱 chunk + 关键词 chunk 双路索引
- 检索增强：混合检索 + Reranker 内置

---

## 3️⃣ Coze（扣子）实战

```
1. https://www.coze.cn 注册
2. 创建 Bot → 设定人设 + 选择 LLM
3. 添加 Plugin（搜索/图片生成/代码执行）
4. 添加 Knowledge（上传文档）
5. 配置 Workflow（可视化编排）
6. 发布到豆包/微信/API
```

---

## 4️⃣ 自建 vs 低代码平台选择

| 场景 | 推荐方案 | 原因 |
|------|---------|------|
| 快速验证想法 | Coze / Dify | 0 代码，半天出 Demo |
| 企业内部知识库 | Dify + RAGFlow | 开源可控 + 深度文档解析 |
| 复杂 Agent 逻辑 | 自建 LangGraph | 平台编排能力有限 |
| 简历项目 | 自建 + 平台各做一个 | 展示不同能力维度 |

---

## ✅ 产出物 Checklist

- [ ] Docker 部署 Dify 社区版
- [ ] 搭建一个"知识库问答"Agent 并调通 API
- [ ] 了解 RAGFlow 的文档解析能力
- [ ] 在 Coze 上创建一个 Bot
