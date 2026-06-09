# Phase 1 💬 Prompt、API 与商业 LLM 网关雏形

> **Day 6-15** | ⏱️ 10 天 | 📊 难度 ⭐⭐

---

## 你将在本阶段学会什么

- ✅ 编写 25+ 个可直接复制的 Prompt 模板（6 大类场景）
- ✅ 接入 5+ 厂商 API（OpenAI/DeepSeek/Qwen/Claude/Gemini）
- ✅ 封装统一 LLM 客户端（工厂模式 + 流式/非流式统一接口）
- ✅ 搭建 FastAPI 聊天服务（OpenAI 兼容格式 + SSE 流式）
- ✅ Vue3 + TypeScript SSE 流式前端
- ✅ Token 计费管控 + 多模型容灾路由 + 统一鉴权

## 前置要求

- 完成 [Phase 0](../phase0_foundation/)（Python/Docker/Git 基础）
- 注册至少一个 LLM 厂商的 API Key（推荐从 DeepSeek 开始，便宜）

## 学习天数与任务表

| Day | 主题 | 文件 | 产出 | ✅ |
|:---:|:-----|:-----|:-----|:--:|
| 6-7 | Prompt Cookbook | `01_prompt_cookbook.md` | 25+ 可复制 Prompt 模板 | ☐ |
| 7-8 | Prompt 进阶 | `05_prompt_advanced.md` | CoT/结构化/Few-shot | ☐ |
| 8-9 | 多厂商 API 接入 | `02_llm_client.md` | 5+ Provider 实现 | ☐ |
| 9-10 | 统一 LLM 客户端 | `02_llm_client.md` | 工厂模式 + 流式/非流式 | ☐ |
| 10-11 | Token 计费管控 | `02_llm_client.md` | Token 计数 + 成本估算 | ☐ |
| 11-12 | 多模型容灾路由 | `02_llm_client.md` | fallback 降级逻辑 | ☐ |
| 12 | 统一鉴权网关 | `07_env_secrets_mgmt.md` | API Key 管理 + 防攻击 | ☐ |
| 12-13 | FastAPI 聊天服务 | `03_fastapi_chat.md` + `llm_chat_service/` | 可运行的 API 服务 | ☐ |
| 14-15 | Web Chat Demo | `04_web_chat_demo.md` | Vue3 SSE 前端 | ☐ |
| 15 | 测试指南 | `08_testing_guide.md` | pytest 异步测试 | ☐ |

## 本阶段核心产出

- 🤖 **Unified LLM Client**：一行代码切换 Provider
- ⚡ **FastAPI Chat Service**：兼容 OpenAI 格式的 API
- 🌐 **Web Chat Demo**：Vue3 SSE 流式聊天界面
- 💰 **Token 计费引擎**：多厂商成本实时估算

## 如何运行本阶段 Demo

```bash
# FastAPI 聊天服务
cd phase1_prompt_api/llm_chat_service
cp .env.example .env          # 填入你的 API Key
pip install fastapi uvicorn httpx openai pydantic python-dotenv
uvicorn app.main:app --reload --port 8000

# 测试
curl http://localhost:8000/healthz
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"你好"}],"stream":false}'
```

> 🚧 **注意**: `llm_chat_service/` 当前仅有项目骨架，完整实现正在补全中。代码示例见 `03_fastapi_chat.md`。

## 验收标准

- [ ] 能用 Prompt Cookbook 中的模板调通至少 2 个厂商
- [ ] 写出工厂模式 LLM Client，切换 Provider 只改一行代码
- [ ] 启动 FastAPI 服务，用 curl 测试流式和非流式
- [ ] 理解 SSE 协议格式（`data: {json}\n\n`）
- [ ] 算出一次 API 调用的 Token 消耗和费用

## 常见问题

| 问题 | 解决 |
|:-----|:-----|
| OpenAI API 403 | 检查 API Key 是否正确 + 是否有余额 |
| DeepSeek API 超时 | DeepSeek 有时慢，timeout 设 60s |
| SSE 流式收不到数据 | 检查 `Content-Type: text/event-stream` 和 `Cache-Control: no-cache` |
| 前端跨域 | Vite 开发服务器配 proxy，生产用 Nginx |

## 面试可讲点

1. "我封装了 5 个厂商的统一调用层，抽象基类 + 工厂模式"
2. "我理解 SSE 协议的字节流边界问题——buffer 缓存拼接"
3. "我用 `secrets.compare_digest` 做常量时间 API Key 比较，防时序攻击"

## 下一阶段

👉 [Phase 2: 大模型底层硬核拆解 + 工业微调与部署](../phase2_llm_internals/)
