# 🏭 05 — 开源 Agent 平台实战：Dify / RAGFlow / Coze

> 🎯 **目标**：掌握三平台部署与使用，知道什么时候用平台、什么时候自建。
> ⏱️ 预计时间：2 天

---

## 📋 三平台对比

| 维度 | Dify | RAGFlow | Coze（扣子） |
|:-----|:-----|:--------|:-----------|
| 定位 | 可视化 LLM 应用 | 深度文档理解 RAG | Agent 搭建平台 |
| 开源 | ✅ Apache 2.0 | ✅ Apache 2.0 | ❌ 字节跳动 SaaS |
| RAG 能力 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Agent 能力 | ⭐⭐⭐⭐（Chatflow/Workflow） | ⭐⭐ | ⭐⭐⭐⭐ |
| 部署难度 | ⭐⭐ Docker 一键 | ⭐⭐ Docker 一键 | ⭐ 无需部署 |
| 插件生态 | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| 国内访问 | ✅ | ✅ | ✅ 国内版 coze.cn |
| 适合场景 | 企业知识库+工作流 | 复杂文档解析 RAG | 快速验证 Bot 想法 |

---

## 1️⃣ Dify 深度实战

```bash
# Docker 部署（社区版）
git clone https://github.com/langgenius/dify.git
cd dify/docker
cp .env.example .env
docker compose up -d
# 访问 http://localhost:3000
```

### 知识库问答 Chatflow 搭建

```
完整流程:
1. 知识库 → 上传 Phase 2 笔记（Markdown/PDF）
   → 设置分段规则（500字/overlap 50）→ 索引
2. 创建应用 → 选择 "Chatflow"（比 Chatbot 更灵活）
3. 编排节点:
   [开始] → [知识检索] → [LLM 生成] → [回答]
         → [条件分支: 检索分数<0.5?] → [直接回答+标注无资料]
4. 配置 LLM: 选 DeepSeek V3（便宜）或 GPT-4o（质量）
5. 测试 → 发布 → 获取 API Key
```

### Dify API 调用

```python
import requests

DIFY_API_URL = "http://localhost:3000/v1/chat-messages"

# 非流式
resp = requests.post(DIFY_API_URL,
    headers={
        "Authorization": "Bearer app-xxxxxxxxxxxxx",
        "Content-Type": "application/json",
    },
    json={
        "query": "什么是 Transformer？",
        "user": "user-001",
        "response_mode": "blocking",
    },
)
print(resp.json()["answer"])

# 流式
resp = requests.post(DIFY_API_URL,
    headers={"Authorization": "Bearer app-xxx"},
    json={"query": "解释 KV Cache", "user": "user-001", "response_mode": "streaming"},
    stream=True,
)
for line in resp.iter_lines():
    if line.startswith(b"data: "):
        chunk = json.loads(line[6:])
        print(chunk.get("answer", ""), end="")
```

### Dify 适合 vs 不适合

| ✅ 适合 | ❌ 不适合 |
|:--------|:---------|
| 企业知识库问答 | 需要复杂状态机的 Agent |
| 多轮对话客服 | 需要自定义工具调用逻辑 |
| 快速验证 RAG 想法 | 需要精确控制 Prompt 链 |
| 非技术人员维护 | 需要细粒度限流/计费 |

---

## 2️⃣ RAGFlow 深度实战

```bash
git clone https://github.com/infiniflow/ragflow.git
cd ragflow/docker
# 调内存（RAGFlow 很吃内存，建议 16GB+）
sed -i 's/MEM_LIMIT=8G/MEM_LIMIT=16G/' docker-compose.yml
docker compose up -d
# 访问 http://localhost:80
```

### RAGFlow 独特能力

| 能力 | 说明 | 对比 Dify |
|:-----|:-----|:--------|
| **深度文档解析** | PDF 表格提取/双栏排版/扫描件 OCR | Dify 用 Unstructured，RAGFlow 自研更强 |
| **知识图谱 Chunk** | 实体识别 + 关系抽取，构建 KG chunk | Dify 无此能力 |
| **混合 Chunk 索引** | 关键词 chunk + 语义 chunk 双路索引 | Dify 只有语义 chunk |
| **RAPTOR 摘要** | 递归摘要生成多层级索引 | Dify 无 |
| **内置 Reranker** | 检索后自动精排 | Dify 需手动配置 |

### RAGFlow 使用流程

```
1. 创建知识库 → 配置解析器（选 DeepDoc）
2. 上传文档（PDF/Word/Excel/PPT/图片）
3. 等待解析（RAGFlow 会自动识别表格/图片/排版）
4. 配置 Chunk 方式 → 开始索引
5. 创建 Chat → 关联知识库 → 选择 LLM
6. 测试问答 + API 调用
```

```python
# RAGFlow API
resp = requests.post("http://localhost:80/api/v1/chats/chat_id/completions",
    headers={"Authorization": "Bearer ragflow-xxx"},
    json={"question": "什么是 Attention？", "stream": True},
    stream=True,
)
```

---

## 3️⃣ Coze（扣子）实战

```
国内版: https://www.coze.cn
国际版: https://www.coze.com

创建 Bot 流程:
1. 人设与回复逻辑:
   "你是一个大模型技术助手，帮助初学者理解 Transformer/RAG/Agent。
    回答风格：先一句话总结，再详细解释，最后给学习建议。"
2. 插件配置:
   - 必应搜索（联网检索最新信息）
   - 代码执行器（运行 Python 验证概念）
   - 图片理解（多模态输入）
3. 知识库:
   上传 Phase 2 笔记，作为回答的参考素材
4. Workflow（可选）:
   开始→意图识别→[简单问题:直接回答|复杂问题:搜索+整理]→输出
5. 发布:
   - 豆包 App（免费流量）
   - 微信客服/公众号
   - API 调用
```

---

## 4️⃣ 自建 vs 平台决策树

```
你的需求是什么？
├── 快速验证一个 RAG 想法 → Coze（5分钟出 Demo）
├── 企业内部知识库，文档复杂 → RAGFlow（深度文档解析）
├── 需要可视化编排+多模型切换 → Dify（最均衡）
├── 复杂 Agent 逻辑+自定义工具 → 自建 LangGraph
├── 简历项目 → 自建 + 平台各做一个（展示选择能力）
└── 生产级高并发+精细化控制 → 自建 FastAPI + AI-Gateway
```

---

## 5️⃣ 面试怎么讲

> "我不仅会自己写 Agent，还在 Dify、RAGFlow、Coze 三个主流平台上搭建过工作流。
> 我清楚什么时候该用平台快速验证，什么时候该自建 LangGraph。
> 比如文档解析密集的场景选 RAGFlow，快速验证 Bot 用 Coze，复杂多步推理必须自建。"

---

## ✅ 产出物 Checklist

- [ ] Docker 部署 Dify 社区版并跑通一个 Chatflow
- [ ] Docker 部署 RAGFlow 并体验其文档解析能力
- [ ] 在 Coze 上创建一个 Bot 并发布
- [ ] 输出三平台对比笔记（适合场景+限制+成本）
