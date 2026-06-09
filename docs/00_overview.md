# 100-Day LLM Engineering Roadmap：从本地推理、RAG、Agent 到高并发 AI-Gateway

本项目专为具备一定编程基础的本科生设计，100 天从环境基建、Prompt 工程、大模型底层原理，到 RAG 知识库、Agent 工作流、9 大开源项目冲刺，最终手搓并部署一个企业级多模型 AI-Gateway。

---

## 适合人群

- 有 Python 基础的本科生
- 想入门大模型应用开发的同学
- 不想只停留在"调用 API"阶段的学习者
- 想做出一个能放进简历和作品集的完整 AI 工程项目

---

## 你将学到什么（技能矩阵）

### A. 工程基建能力
| 技能 | 掌握程度 | 所在阶段 |
|---|---|---|
| Git / GitHub | 分支协作、PR、Conventional Commits | Phase 0 |
| Linux / Shell | 常用命令、进程管理、日志排查、权限 | Phase 0 |
| SSH | 密钥配置、免密登录、远程开发、端口转发 | Phase 0 |
| Conda / pip / uv | 虚拟环境、依赖锁定、 channels | Phase 0 |
| Docker | Dockerfile、Compose、网络、Volume、多阶段构建 | Phase 0 |
| Nginx | 反向代理、负载均衡、SSL 终结 | Phase 6 |
| CI/CD (GitHub Actions) | 自动测试、自动构建镜像 | Phase 6 |
| 环境变量与密钥管理 | .env、secrets、配置分离 | Phase 0 |

### B. 后端与数据基建
| 技能 | 掌握程度 | 所在阶段 |
|---|---|---|
| FastAPI | 路由、中间件、依赖注入、后台任务 | Phase 1 |
| Pydantic | Schema 校验、配置管理 | Phase 1 |
| Redis | 缓存、Pub/Sub、限流、会话存储 | Phase 0 / 6 |
| PostgreSQL / MySQL | 表设计、索引、Alembic 迁移 | Phase 0 / 6 |
| 向量数据库 (FAISS / Chroma / Milvus) | 索引构建、持久化、相似检索 | Phase 3 |

### C. 大模型使用能力
| 技能 | 掌握程度 | 所在阶段 |
|---|---|---|
| Prompt Engineering | Zero/Few-shot、CoT、结构化输出、约束 | Phase 1 |
| 主流 API 调用 | OpenAI / DeepSeek / Qwen / Claude / Gemini | Phase 1 |
| Token 计费与上下文管理 | 计数、截断、压缩、成本估算 | Phase 1 |
| Streaming / SSE | 流式输出、断线恢复、EventSource | Phase 1 |
| Function Calling / Tool Calling | 工具定义、调用循环、结果处理 | Phase 5 |
| AI 编程工作流 | Claude Code / Cursor 高阶用法 | Phase 1 |

### D. 大模型底层原理
| 技能 | 掌握程度 | 所在阶段 |
|---|---|---|
| Transformer 架构 | Self-Attention、FFN、LayerNorm、Residual | Phase 2 |
| 注意力机制 | MHA / MQA / GQA、Attention Mask | Phase 2 |
| 位置编码 | RoPE、ALiBi、上下文扩展 | Phase 2 |
| KV Cache | Prefill / Decode、显存估算 | Phase 2 |
| MoE | Expert Router、Top-k 路由、稀疏激活 | Phase 2 |
| 量化 | FP16/BF16/INT8/INT4、GPTQ/AWQ/GGUF | Phase 2 |
| LoRA / QLoRA | 低秩适配、数据准备、合并部署 | Phase 2 |

### E. RAG 检索增强体系
| 技能 | 掌握程度 | 所在阶段 |
|---|---|---|
| 文档解析 | PDF、Markdown、HTML、Word、表格、OCR | Phase 3 |
| Chunk 策略 | 固定/语义/递归切分、Overlap、Metadata | Phase 3 |
| Embedding | 模型选型、相似度计算、Batch 处理 | Phase 3 |
| 向量检索 | FAISS、Chroma、Top-k、MMR | Phase 3 |
| 混合检索 | BM25 + Vector + Reranker | Phase 3 |
| LangChain RAG | Chain、Retriever、Tool、Memory | Phase 3 |
| LangGraph RAG | StateGraph、条件边、循环、Checkpoint | Phase 3 |
| LlamaIndex | Document、Node、Index、Query Engine | Phase 4 |
| GraphRAG | 实体抽取、图谱构建、社区摘要、全局检索 | Phase 4 |
| RAG 评估 | 召回率、忠实性、引用准确率、幻觉检测 | Phase 3 |

### F. Agent 智能体
| 技能 | 掌握程度 | 所在阶段 |
|---|---|---|
| ReAct | 思考-行动-观察循环 | Phase 5 |
| Tool Calling | 搜索、文件、代码执行工具 | Phase 5 |
| LangGraph Agent | 多节点、Human-in-the-loop、重试恢复 | Phase 5 |
| SWE-agent | 代码定位、编辑、测试反馈闭环 | Phase 4 |
| Agent 安全 | 权限控制、Prompt Injection 防御、审计 | Phase 5 |

### G. 多模态
| 技能 | 掌握程度 | 所在阶段 |
|---|---|---|
| CLIP | 图文对齐、视觉特征提取 | Phase 4 |
| Diffusers | SD/SDXL Pipeline、LoRA、ControlNet | Phase 4 |
| SAM 2 | 图像/视频分割、Mask 工程 | Phase 4 |
| Qwen-VL | 中文 OCR、文档理解、图表问答 | Phase 4 |
| LLaVA | VLM 架构、Visual Instruction Tuning | Phase 4 |

### H. 工程化与网关
| 技能 | 掌握程度 | 所在阶段 |
|---|---|---|
| 统一模型路由 | 多 Provider、Fallback、优先级 | Phase 6 |
| API Key 管理 | 认证、密钥池轮询 | Phase 6 |
| 限流 | 令牌桶、滑动窗口、Redis 实现 | Phase 6 |
| 熔断降级 | Circuit Breaker、超时控制 | Phase 6 |
| 计费系统 | Token 统计、用户额度、成本估算 | Phase 6 |
| 日志与监控 | 结构化日志、TTFT、tokens/s、错误率 | Phase 6 |
| Dashboard | Vue3 + TypeScript 大屏 | Phase 6 |
| Docker Compose 部署 | 一键启动全套服务 | Phase 6 |

---

## 100 天路线总览

```
Phase 0: 工程师基建与极速复习          Day 1  - Day 5    (5 天)
Phase 1: Prompt、API 与 AI 编程生产力   Day 6  - Day 15   (10 天)
Phase 2: 大模型底层硬核拆解             Day 16 - Day 28   (13 天)
Phase 3: RAG 检索增强体系               Day 29 - Day 45   (17 天)
Phase 4: 九大开源项目极限冲刺           Day 46 - Day 75   (30 天)
Phase 5: Agent 与工作流架构             Day 76 - Day 84   (9 天)
Phase 6: 终极项目 AI-Gateway            Day 85 - Day 100  (16 天)
```

---

## Phase 0：工程师基建与极速复习（Day 1 - Day 5）

> 目标：建立坚不可摧的工程开发环境，用最短时间唤醒 Python 与深度学习记忆。

### Day 1：Git、GitHub 与 SSH

**学习内容：**

- Git 核心概念：repo、commit、branch、merge、rebase、stash
- GitHub 工作流：Fork → Clone → Branch → PR → Review → Merge
- Conventional Commits 规范：`feat:` `fix:` `docs:` `refactor:`
- .gitignore 编写（Python 项目通用模板）
- SSH 密钥生成：`ssh-keygen -t ed25519 -C "your_email"`
- SSH config 配置多主机别名与密钥
- 远程服务器免密登录
- VSCode Remote SSH 开发

**产出物：**
- 创建 GitHub 仓库 `llm-fullstack-roadmap`
- 完成 README.md 初版与 .gitignore
- SSH 配置好 GitHub + 一台远程服务器（如有）

---

### Day 2：Python 工程复习

**学习内容：**

- Python 基础语法回顾（列表推导式、生成器、装饰器、上下文管理器）
- 函数 / 类 / 模块化组织
- 类型注解（`typing` 模块）：`List`, `Dict`, `Optional`, `Union`, `Callable`
- 异步编程基础：`async`/`await`、`asyncio`（为 FastAPI 做准备）
- 异常处理：`try/except/finally`、自定义异常
- 文件读写：文本、JSON、CSV、二进制
- 虚拟环境：`conda create`、`conda activate`、`pip freeze`
- 依赖管理：`requirements.txt` 与 `pyproject.toml` 的区别

**产出物：**
- 完成 `notebooks/day01_python_review.ipynb`
- 写一个 CLI 工具脚本：读取文件并统计 token/字数

---

### Day 3：深度学习极速复习

**学习内容：**

- 张量（Tensor）：创建、维度、索引、广播
- 自动求导（Autograd）：`requires_grad`、`backward()`、计算图
- 反向传播直觉：链式法则如何更新参数
- 损失函数：MSE、CrossEntropy、BCE
- 优化器：SGD、Adam、AdamW
- 模型结构回顾：MLP → CNN → RNN → LSTM → Transformer（概念级）
- PyTorch 数据流：`Dataset` → `DataLoader` → `model` → `loss` → `optimizer`

**产出物：**
- 完成 `notebooks/day02_pytorch_review.ipynb`
- 训练一个最小分类模型（如 MNIST 或 Iris）

---

### Day 4：Linux / Shell / 环境管理

**学习内容：**

- 常用 Shell 命令：`ls`, `cd`, `pwd`, `cp`, `mv`, `rm`, `mkdir`, `chmod`, `chown`
- 文本处理：`grep`, `awk`, `sed`, `head`, `tail`, `cat`, `less`
- 进程管理：`ps`, `top`, `htop`, `kill`, `nohup`, `&`, `fg`, `bg`
- 磁盘与内存：`df -h`, `du -sh`, `free`
- 端口与网络：`lsof -i :端口号`, `netstat`, `curl`, `ping`
- 日志查看：`tail -f`, `journalctl`
- 环境变量：`.env` 文件、`export`、`source`
- conda 深度使用：`environment.yml`、channels、mamba 加速、常见坑
- uv（新一代 Python 包管理器）基础
- 模型文件管理：下载、校验、目录组织、软链接

**产出物：**
- 写一份 `docs/01_environment_setup.md`（环境搭建完整指南）
- 整理 `docs/05_troubleshooting.md`（常见环境报错与解决方案）

---

### Day 5：Docker 与中间件入门

**学习内容：**

- Docker 核心概念：镜像（Image）、容器（Container）、Dockerfile
- 常用命令：`docker build`, `docker run`, `docker ps`, `docker logs`, `docker exec`
- Dockerfile 编写：`FROM`, `RUN`, `COPY`, `WORKDIR`, `CMD`, `ENTRYPOINT`
- 多阶段构建（Multi-stage Build）：减小镜像体积
- Docker Compose：`services`, `networks`, `volumes`, `depends_on`, `healthcheck`
- Volume 数据持久化：bind mount vs named volume
- Network：bridge、host、容器间通信
- .env 注入到容器
- Redis 快速上手：启动容器、基本命令（`SET/GET/DEL/EXPIRE`）、Pub/Sub 概念
- PostgreSQL 快速上手：启动容器、基本 SQL（建表、查询、插入）

**产出物：**
- 编写 `docker-compose.yml`：启动 FastAPI + Redis + PostgreSQL
- 验证服务间可以互相通信

---

## Phase 1：Prompt、API 与 AI 编程生产力（Day 6 - Day 15）

> 目标：在深入底层之前，先成为顶尖的"大模型使用者"和 AI 辅助开发者。

### Day 6：Prompt Engineering 基础

**学习内容：**

- Zero-shot：不提供示例，直接给出任务描述
- Few-shot：提供 2-5 个示例，让模型遵循格式
- 角色设定（System Prompt）：定义模型行为边界
- 任务拆解：把复杂任务拆成子步骤
- 格式约束：要求输出 JSON、Markdown、表格
- 上下文管理：什么时候该给背景信息、给多少

**产出物：**
- 整理 20 个常用 Prompt 模板（翻译、总结、分类、代码生成、改写等）

---

### Day 7：Prompt Engineering 进阶

**学习内容：**

- Chain-of-Thought (CoT)：让模型"一步一步思考"
- Self-Consistency：多次采样取多数答案
- 反思式 Prompt（Reflexion）：让模型自我检错
- 结构化输出：Pydantic + Function Calling 约束 JSON Schema
- 约束型 Prompt：禁止输出某些内容、限制长度、要求引用
- 长文本总结 Prompt：分片总结再合并
- 代码审查 Prompt：让模型帮你 review 代码

**产出物：**
- 构建 `prompt_templates/` 目录
- 完成 Prompt Cookbook（每种技术配 3 个示例）

---

### Day 8：主流大模型 API 调用

**学习内容：**

- OpenAI 风格接口规范：`/v1/chat/completions`
- 对接模型：OpenAI (GPT-4o)、DeepSeek (V3/R1)、Qwen (通义千问)、Claude、Gemini
- `messages` 格式：`system` / `user` / `assistant` / `tool`
- 核心参数：`temperature` / `top_p` / `max_tokens` / `stop`
- 流式输出（Streaming）：`stream=True`、`chunk` 解析
- 错误处理：Rate Limit、Timeout、Context Length Exceeded

**产出物：**
- 实现一个统一的 `LLMClient` 类
- 支持普通输出和流式输出两种模式

---

### Day 9：Token 计算与上下文管理

**学习内容：**

- Token 是什么：BPE 分词原理（概念级）
- `tiktoken` 库使用：精确计算 token 数
- 上下文窗口限制：各模型的 context window 对比
- 输入成本 vs 输出成本：不同模型的定价差异
- 长上下文截断策略：保留头部 + 尾部、滑动窗口
- 历史消息自动压缩：保留最近 N 轮 + 总结早期对话

**产出物：**
- 实现 `token_counter.py`（精确计费和截断）
- 实现对话历史自动裁剪工具

---

### Day 10：AI 编程工具流

**学习内容：**

- Claude Code：如何让它读项目、修 Bug、生成测试、写文档
- Cursor：Tab 补全、Cmd+K 编辑、Composer 多文件编辑
- GitHub Copilot：何时信任、何时复查
- 工程级任务提示词写法：不是"帮我写个函数"，而是"在 xx 文件中，遵循 xx 模式，添加 xx 功能，同时更新 yy 测试"
- 如何让 AI 审查代码：给出 diff → 要求按 checklist 审查
- AI 辅助写单元测试

**产出物：**
- 写一份 `docs/ai_coding_workflow.md`
- 整理 5 个常用的本地 Agent 执行提示词模板

---

### Day 11：FastAPI 服务封装（上）

**学习内容：**

- FastAPI 核心概念：路由、路径参数、查询参数、请求体
- Pydantic v2：`BaseModel`、`Field`、validator
- 请求/响应 Schema 设计
- 依赖注入（Dependency Injection）：`Depends()`
- 自动生成 Swagger 文档：`/docs`
- 启动服务：`uvicorn`

**产出物：**
- 搭建 FastAPI 项目骨架
- 定义 `/v1/chat/completions` 接口 Schema（兼容 OpenAI 格式）

---

### Day 12：FastAPI 服务封装（下）

**学习内容：**

- 中间件（Middleware）：请求日志、CORS、异常捕获
- 异常处理器（Exception Handler）：统一错误响应格式
- 后台任务（Background Tasks）：异步记录日志
- 异步接口：`async def`、`await`、数据库异步操作
- 请求验证：Pydantic 自动校验
- 响应序列化：`response_model`

**产出物：**
- 完成 `/v1/chat/completions` 接口实现
- 统一错误格式：`{"error": {"code": "...", "message": "..."}}`

---

### Day 13：流式输出（SSE）

**学习内容：**

- Server-Sent Events (SSE) 协议：`text/event-stream`
- FastAPI `StreamingResponse` 实现
- `sse-starlette` 库使用
- 前端 `EventSource` API 消费 SSE
- 流式异常处理：中途断线、模型超时
- 对比 WebSocket：何时用 SSE、何时用 WebSocket

**产出物：**
- 实现 SSE 流式聊天接口 `/v1/chat/completions` (stream=true)
- 写一个最小 HTML 页面验证流式输出

---

### Day 14 - Day 15：最小聊天 Web 应用

**学习内容：**

- Vue3 基础：组件、`ref`、`reactive`、`computed`、`watch`
- 前端调用 SSE：`fetch` + `ReadableStream` 或 `EventSource`
- 消息列表渲染、Markdown 渲染
- 错误重试与加载状态
- 请求日志记录（服务端 + 客户端）

**产出物：**
- 完成一个极简 Web Chat Demo
- 支持多轮对话 + 流式输出

---

## Phase 2：大模型底层硬核拆解（Day 16 - Day 28）

> 目标：理解 LLM 的核心机制。不要求从零训练大模型，但要清楚推理、显存、量化、微调到底在做什么。

### Day 16：Transformer 架构总览

**学习内容：**

- 整体架构：Input → Embedding → N×Decoder Layer → LM Head → Output
- Token Embedding：把 token ID 映射成向量
- Self-Attention 直觉：每个 token "看"序列中所有 token
- Feed-Forward Network (FFN)：对每个 token 独立做非线性变换
- Layer Normalization：稳定训练
- Residual Connection：缓解梯度消失
- Decoder-only vs Encoder-Decoder：GPT 为什么只用 Decoder

**产出物：**
- 手绘/用工具画一张完整的 Transformer Decoder 架构图
- 标注每层的输入输出 shape

---

### Day 17：Attention 深度拆解

**学习内容：**

- Q / K / V 的含义：Query 是我在找什么，Key 是我有什么，Value 是实际内容
- Scaled Dot-Product Attention 公式推导
- Multi-Head Attention (MHA)：多组 Q/K/V 并行
- Multi-Query Attention (MQA)：所有 Head 共享一组 K/V（省显存）
- Grouped-Query Attention (GQA)：折中方案（主流模型标配）
- Attention Mask：Causal Mask（防止看到未来 token）、Padding Mask

**产出物：**
- 用 PyTorch 手写一个简化版 Multi-Head Attention（约 50 行）
- 对比 MHA / MQA / GQA 的显存占用计算

---

### Day 18：位置编码与长上下文扩展

**学习内容：**

- 为什么需要位置编码：Attention 本身不感知顺序
- 绝对位置编码（Sinusoidal / Learned）
- RoPE（旋转位置编码）：核心思想、数学直觉、为什么主流模型都用它
- ALiBi：用 bias 替代 position embedding
- 上下文扩展技术：NTK-aware、YaRN、Self-Extend
- 长上下文退化问题："Lost in the Middle"

**产出物：**
- 写 `notes/rope.md`：RoPE 的数学推导与直觉解释
- 对比几种位置编码的优缺点

---

### Day 19：KV Cache 与推理加速

**学习内容：**

- 推理两阶段：Prefill（预填充）vs Decode（逐 token 解码）
- 为什么 Decode 阶段要缓存 K/V：避免重复计算
- KV Cache 显存估算公式：`2 × layers × hidden_dim × seq_len × dtype_bytes`
- 影响因子：batch size、seq length、dtype、模型大小
- PagedAttention（vLLM 核心）：把 KV Cache 分页管理，减少碎片
- Continuous Batching：动态加入/移除请求

**产出物：**
- 写一篇分析：为什么首 token 慢（TTFT 高）、后续 token 快
- 计算一个 7B 模型在不同上下文长度下的 KV Cache 显存占用

---

### Day 20：MoE（混合专家模型）

**学习内容：**

- MoE 核心思想：不是所有参数都参与每次推理
- Expert（专家）：多个独立的 FFN 子网络
- Router / Gate：根据 token 选择激活哪几个 Expert
- Top-k 路由：选 top-1 还是 top-2
- 稀疏激活：每次只激活少量 Expert（省计算）
- 负载均衡：避免某些 Expert 被频繁选中
- 代表模型：DeepSeek-V3/R1、Mixtral 8×7B

**产出物：**
- 写 `notes/moe_intro.md`：MoE 为什么能用更少计算跑更大模型
- 对比 Dense Model vs MoE Model 的推理特性

---

### Day 21 - Day 22：量化技术

**学习内容：**

- 数值精度回顾：FP32 vs FP16 vs BF16 vs INT8 vs INT4
- 量化本质：把高精度权重映射到低精度
- 对称量化 vs 非对称量化
- GPTQ：基于 Optimal Brain Quantization 的后训练量化
- AWQ：Activation-Aware Weight Quantization（保护重要通道）
- GGUF：llama.cpp 生态的量化格式（Q4_K_M、Q5_K_M 等）
- 量化对推理速度、显存占用、回答质量的影响
- 如何选择量化级别：内存预算 → 量化格式

**产出物：**
- 对比同一模型在 FP16 / INT8 / INT4 / Q4_K_M 下的：
  - 模型文件大小
  - 加载后显存占用
  - 推理速度 (tokens/s)
  - 回答质量（人工评分）

---

### Day 23 - Day 25：本地推理实战

**学习内容：**

- **Ollama**：最简单本地推理入口，`ollama pull`、`ollama run`、Modelfile
- **llama.cpp**：GGUF 格式加载、llama-server、OpenAI-compatible endpoint
- **MLX LM**：Apple Silicon 原生推理与微调（如果你用 Mac）
- **vLLM**：高吞吐推理引擎，PagedAttention、Continuous Batching
- 对比四种推理方案：速度、显存、易用性、OpenAI 兼容程度

**产出物：**
- 至少启动两种本地模型服务（如 Ollama + llama.cpp server）
- 用 Python 脚本分别调用本地模型和云端 API，对比延迟
- FastAPI Gateway 成功调用本地模型端点

---

### Day 26 - Day 28：LoRA / QLoRA 微调基础

**学习内容：**

- 全量微调 vs 参数高效微调（PEFT）
- LoRA 核心思想：在原权重旁加低秩矩阵，只训练新增参数
- LoRA 的数学：`W' = W + α·BA`，其中 B 和 A 是低秩矩阵
- QLoRA：LoRA + 4-bit 量化基础模型（更省显存）
- 关键参数：rank (r)、alpha、target_modules（在哪些层加 LoRA）
- 指令微调数据格式：Alpaca 格式、ShareGPT 格式
- SFT（监督微调）数据准备：清洗、去重、格式统一
- 训练/验证集划分
- 过拟合识别与应对
- LoRA 权重合并与导出部署

**产出物：**
- 完成一个小型身份问答 LoRA 微调 Demo
- 输出合并后的模型，能在本地推理并回答"你是谁"

---

## Phase 3：RAG 检索增强体系（Day 29 - Day 45）

> 目标：从"把文档丢给 LLM"进化到可评估、可调试、可部署的企业级 RAG。

### Day 29：RAG 全流程概览

**学习内容：**

- RAG 完整链路：文档加载 → 清洗 → 切分 → Embedding → 索引 → 检索 → 拼接 Prompt → 生成 → 引用来源
- 为什么需要 RAG：解决知识截止、幻觉、私有数据问题
- Naive RAG vs Advanced RAG vs Modular RAG
- RAG 的典型失败模式：检索不到、检索到不相关的、生成时忽略证据

**产出物：**
- 实现一个 `naive_rag.py`：完整跑通 RAG 全流程
- 用一段你的项目文档做测试

---

### Day 30 - Day 31：文档解析

**学习内容：**

- 多格式加载：PDF (`pymupdf`)、Markdown、HTML、Word (`python-docx`)、TXT
- PDF 解析的坑：扫描件 vs 文字型 PDF、双栏排版、表格、水印
- 元数据提取：文件名、页码、标题层级、创建时间
- 文档清洗：去空格、去页眉页脚、去特殊字符、统一换行
- OCR 基础概念：Tesseract、PaddleOCR（什么时候需要）
- 表格提取：CSV 结构化、Markdown 表格格式

**产出物：**
- 实现 `document_loader.py`：支持 PDF + Markdown + TXT
- 每条 chunk 附带元数据（来源、页码、标题）

---

### Day 32 - Day 33：Embedding 与向量数据库

**学习内容：**

- Embedding 模型选型：
  - 英文：`BAAI/bge-large-en-v1.5`、`sentence-transformers`
  - 中文：`BAAI/bge-large-zh-v1.5`、`text2vec-large-chinese`
  - 多语言：`intfloat/multilingual-e5-large`
- 余弦相似度 vs 欧氏距离 vs 点积
- FAISS：本地向量索引构建、`IndexFlatIP`、`IndexIVFFlat`
- Chroma：轻量级向量数据库，持久化存储
- Milvus / Qdrant（了解）：生产级向量数据库
- 向量索引持久化与增量更新

**产出物：**
- 实现本地知识库索引
- 支持添加文档、重建索引、相似检索

---

### Day 34 - Day 35：检索增强技术

**学习内容：**

- 基础检索：Top-k 向量相似度检索
- MMR (Maximal Marginal Relevance)：平衡相关性与多样性
- Hybrid Search（混合检索）：BM25（关键词） + Vector（语义）
- BM25 原理与实现：`rank_bm25`
- Reranker（重排序）：`BAAI/bge-reranker` 对 Top-k 结果二次排序
- Query Rewrite（查询改写）：让 LLM 把模糊问题改成检索友好的查询
- Multi-Query Retrieval：生成多个查询变体，合并结果
- 检索结果去重与融合

**产出物：**
- 对比 "Naive Retrieval" vs "Hybrid + Rerank Retrieval" 的检索质量
- 输出对比报告

---

### Day 36 - Day 38：LangChain / LangGraph RAG

**学习内容：**

- LangChain 核心概念：
  - Document Loader / Text Splitter
  - Embeddings / VectorStore / Retriever
  - Chain：`LCEL`（LangChain Expression Language）
  - Tool：把检索器封装成 Tool
  - Memory：对话历史管理
- LangGraph 核心概念：
  - StateGraph：定义一个状态的流转
  - Node：每个处理步骤
  - Edge / Conditional Edge：连接步骤、条件跳转
  - Checkpoint：保存中间状态（支持断点续跑）
  - 循环与错误恢复

**产出物：**
- 实现一个 LangGraph RAG 流程：
  `Query → Rewrite → Retrieve → Judge Doc Relevance → Rerank → Generate → Verify Citations → Output`
- 当检索不到相关文档时，走 fallback 路径

---

### Day 39 - Day 40：LlamaIndex RAG

**学习内容：**

- LlamaIndex 核心抽象：
  - `Document` / `Node`：文档与节点
  - `Index`：索引结构
  - `Retriever`：检索器
  - `QueryEngine`：查询引擎
  - `ResponseSynthesizer`：回答合成器
- 数据连接器（Data Connectors）：从 Notion、Slack、GitHub 等加载数据
- LlamaIndex vs LangChain：各自的强项和使用场景
- 子问题查询引擎：把复杂问题拆成子问题，逐一检索再合并

**产出物：**
- 用 LlamaIndex 重写知识库问答 Demo
- 对比 LangChain RAG 和 LlamaIndex RAG 的代码差异

---

### Day 41 - Day 43：RAG 评估

**学习内容：**

- 测试集构建原则：覆盖"能检索到""检索不到""跨文档""需要推理"四类问题
- 检索指标：
  - Recall@K（前 K 个结果覆盖了多少正确答案）
  - MRR（平均倒数排名）
  - Hit Rate（是否至少命中一个正确答案）
- 生成指标：
  - Answer Correctness（答案正确性）
  - Faithfulness（答案是否忠实于检索结果）
  - Citation Accuracy（引用是否准确）
- 幻觉检测：答案中包含的信息是否都能在检索结果中找到
- Ragas 评估框架使用

**产出物：**
- 构建 20 条 QA 测试集
- 用 Ragas 输出完整评估报告：`rag_eval_report.md`

---

### Day 44 - Day 45：RAG Web 应用

**学习内容：**

- 文件上传 API
- 知识库管理：创建/删除/切换知识库
- 流式问答 + 引用展示
- 历史对话管理
- 简单的前端页面

**产出物：**
- 完成一个最小知识库问答 Web App
- 支持上传 PDF → 问答 → 查看引用来源

---

## Phase 4：九大开源项目极限冲刺（Day 46 - Day 75）

> 目标：30 天内复现 9 个主流开源项目，每个项目只抓核心、产出最小可运行 Demo 和避坑记录。
>
> **原则：不要求全量掌握，而是掌握工程入口、最小 Demo、典型坑点、可复用模块。**

### 时间分配总览

| 项目 | 天数 | Day 范围 | 核心产出 |
|---|---|---|---|
| P1: MLX LM | 2 天 | Day 46-47 | 本地推理 + LoRA 微调 |
| P2: llama.cpp | 3 天 | Day 48-50 | GGUF 推理 + 性能压测 |
| P3: Diffusers | 3 天 | Day 51-53 | 文生图 + 图生图 |
| P4: SAM 2 | 3 天 | Day 54-56 | 图像分割 + Mask 服务 |
| P5: Qwen-VL / LLaVA | 4 天 | Day 57-60 | 多模态理解 + OCR |
| P6: LangChain / LangGraph | 4 天 | Day 61-64 | 企业级 RAG 状态机 |
| P7: LlamaIndex | 3 天 | Day 65-67 | 知识库索引与查询 |
| P8: GraphRAG | 4 天 | Day 68-71 | 图谱构建 + 全局检索 |
| P9: SWE-agent | 4 天 | Day 72-75 | 代码修复闭环 |
| **冲刺总结** | **已含在 P9 后** | **Day 75** | **项目矩阵总结** |

---

### Project 1：MLX LM 本地推理与微调（Day 46-47，2 天）

> 核心价值：在 Apple Silicon 上建立本地 LLM 实验底座

**学习内容：**
- MLX 框架定位（Apple Silicon 原生、统一内存）
- 模型加载：从 HuggingFace / mlx-community 下载
- 4-bit 量化模型推理
- LoRA 微调：数据准备、训练、合并
- FastAPI 服务化封装
- 延迟与内存测试

**产出物：**
- `mlx_lm_runbook.md`（复现手册）
- 本地模型推理截图
- LoRA 微调前后对比

---

### Project 2：llama.cpp / GGUF 深度（Day 48-50，3 天）

> 核心价值：掌握本地推理的事实标准底座

**学习内容：**
- GGUF 格式解析：权重 + tokenizer + chat template 合一
- 量化级别对比：Q4_K_M / Q5_K_M / Q8_0 / F16
- llama-server 启动与参数调优
- OpenAI-compatible API endpoint
- Prompt Cache 机制与 slot 管理
- 并发压测：不同 batch size、context length 下的吞吐

**产出物：**
- `llama_cpp_runbook.md`
- 本地 server 启动脚本与配置
- 性能测试记录（延迟矩阵）

---

### Project 3：Diffusers 图像生成（Day 51-53，3 天）

> 核心价值：理解扩散模型 pipeline 工程

**学习内容：**
- Stable Diffusion / SDXL 架构组件：Text Encoder、UNet、VAE、Scheduler
- Pipeline 调用：txt2img、img2img、inpaint
- LoRA 加载与组合
- ControlNet 概念级理解
- IP-Adapter 概念级理解
- Task Schema 设计：seed、steps、cfg_scale、scheduler
- 生成 manifest 记录

**产出物：**
- `diffusers_demo.ipynb`
- 文生图 + 图生图 Demo
- 生成任务 manifest JSON

---

### Project 4：SAM 2 视觉分割（Day 54-56，3 天）

> 核心价值：理解像素级 Mask 工程

**学习内容：**
- SAM 2 核心能力：图像/视频 Promptable Segmentation
- Prompt 方式：Point、Box、Mask
- Mask 输出处理：二值图、RGBA 叠加、多边形轮廓
- Mask 质量检测：面积、连通域、孔洞、边缘平滑度
- 视频分割的 Memory 机制（概念级）
- Mask 作为 AIGC 一等数据类型的设计理念

**产出物：**
- `sam2_segmentation_demo.ipynb`
- Mask 质量检测脚本
- 与 Diffusers inpaint 联动 Demo（SAM 出 mask → Diffusers 局部重绘）

---

### Project 5：Qwen-VL / LLaVA 多模态理解（Day 57-60，4 天）

> 核心价值：打通图文理解与文档智能

**学习内容：**
- Qwen-VL：中文 OCR、文档解析、图表问答
- LLaVA：VLM 架构（Vision Encoder → Projector → LLM）
- 图文问答：描述、计数、空间关系、OCR
- 文档结构化输出：标题、段落、表格、公式
- 图像反推 Prompt（给图 → 输出 SD 的 tag）
- 多模态 Prompt 设计技巧

**产出物：**
- `vision_llm_demo.md`
- 图片问答 Demo（至少覆盖 OCR、图表、描述三类）
- 图像反推 Prompt 实验

---

### Project 6：LangChain / LangGraph 企业级 RAG（Day 61-64，4 天）

> 核心价值：构建可观测、可恢复、可评测的 RAG 系统

**学习内容：**
- LangChain：Retriever、Tool、Memory、LCEL
- LangGraph：StateGraph、条件边、循环、Checkpoint、Human-in-the-loop
- 完整 RAG Agent 状态机：
  `Query → Classify → Rewrite → Retrieve → Rerank → Generate → Verify → Fallback`
- SSE 事件流：每个阶段推送进度事件
- Trace 日志记录：每次检索、生成、验证都可回溯

**产出物：**
- `langgraph_rag_app/` 完整应用
- Trace 日志示例
- 失败恢复演示

---

### Project 7：LlamaIndex 知识库应用（Day 65-67，3 天）

> 核心价值：掌握另一种主流 RAG 框架

**学习内容：**
- Document / Node / Index 抽象
- 多种 Index 类型：VectorStoreIndex、SummaryIndex、KeywordTableIndex
- Query Engine 组合：子问题拆解 + 多引擎融合
- 数据连接器：加载 Notion、GitHub Markdown
- Reranker 集成
- LlamaIndex vs LangChain 的定位差异

**产出物：**
- `llamaindex_knowledge_base/` 完整应用
- 对比报告：同一个任务用 LangChain vs LlamaIndex 的差异

---

### Project 8：GraphRAG 知识图谱检索（Day 68-71，4 天）

> 核心价值：突破传统 RAG 局限，处理全局/多跳/实体关系问题

**学习内容：**
- GraphRAG 核心流程：
  `文档 → 实体抽取 → 关系抽取 → 知识图谱 → 社区检测 → 社区摘要`
- Global Search：回答全局性、总结性问题
- Local Search：回答实体关系、多跳问题
- 实体规范化（解决别名问题）
- GraphRAG vs Vector RAG：各自的适用场景
- 图谱质量评估：实体真实性、关系正确性

**产出物：**
- `graphrag_notes.md` 详细记录
- GraphRAG Demo（用你的项目文档构建图谱）
- GraphRAG vs Naive RAG 对比报告

---

### Project 9：SWE-agent 代码修复 Agent（Day 72-75，4 天）

> 核心价值：理解最接近生产力的 Agent 形态

**学习内容：**
- SWE-agent 核心循环：读 Issue → 搜代码 → 打开文件 → 修改 → 跑测试 → 根据反馈重试
- 代码工具设计：search、open_file、edit_file、run_tests、git_diff
- ReAct 循环在代码修复中的体现
- mini-swe-agent 源码阅读（轻量实现，适合学习）
- 任务构造：准备小型 Python repo + 3-5 个真实 bug
- 评估：resolve rate、patch minimality、regression

**产出物：**
- `code_agent_runbook.md`
- 至少成功修复 1 个 bug 的完整 trace
- 失败案例分析（为什么某些 bug 修不了）

---

### 冲刺总结（Day 75）

**不做新项目，只做三件事：**

1. 每个项目的核心用途一句话总结
2. 每个项目的踩坑记录汇总
3. 标注哪些模块可以接入最终 AI-Gateway、哪些是学习型 Demo

**产出物：**
- `PROJECTS_SUMMARY.md`

---

## Phase 5：Agent 与工作流架构（Day 76 - Day 84）

> 目标：把 Agent 从"会调用工具"升级为"可控、可观测、可恢复"的工作流系统。
>
> 注：Phase 4 的 P6 和 P9 已经打下了 LangGraph 和 SWE-agent 基础，本阶段是在此基础上系统化。

### Day 76 - Day 77：Agent 核心范式

**学习内容：**

- ReAct（Reasoning + Acting）：思考 → 行动 → 观察 → 循环
- Plan-and-Execute：先规划再执行（适合复杂多步任务）
- Tool Calling / Function Calling：
  - 定义 Tool Schema（name、description、parameters）
  - 模型返回 tool_call → 执行工具 → 把结果送回模型
- Agent Memory：短期记忆（对话历史）、长期记忆（向量存储）
- Observation 设计：工具返回什么格式最有利于模型决策

**产出物：**
- 实现一个 Agent：能调用搜索、文件读写、Python 执行三种工具
- 跑通至少 5 个不同任务的 Agent 执行记录

---

### Day 78 - Day 80：LangGraph 状态机 Agent

**学习内容：**

- LangGraph 核心概念回顾：
  - `State`：整个 Agent 的状态数据结构
  - `Node`：每个处理函数
  - `Edge` / `Conditional Edge`：连接与条件跳转
  - `Checkpoint`：断点保存与恢复
  - `Human-in-the-loop`：关键操作暂停等待人工确认
- 多节点 Agent 设计：
  `用户问题 → 任务分类 → 调用工具 → 判断结果 → 不够好则重试 → 生成答案 → 自检 → 输出`
- 错误恢复：工具超时、API 报错、结果格式不符时的 fallback

**产出物：**
- 实现一个完整的 LangGraph Agent
- 包含至少 1 个 Human-in-the-loop 断点
- 支持 checkpoint 恢复（模拟中途断开后继续）

---

### Day 81 - Day 82：Agent 安全

**学习内容：**

- Prompt Injection（提示注入）：
  - 什么是提示注入：用户输入覆盖系统指令
  - 防御策略：输入隔离、指令加固、输出校验
- 工具权限控制：
  - 文件系统：限制读写路径
  - 网络：限制可访问的域名
  - 代码执行：沙箱隔离、超时限制
- 敏感操作确认：删除文件、发送请求、修改配置 → 必须人工确认
- 审计日志：记录每次 tool call 的输入输出

**产出物：**
- `docs/agent_safety.md`：Agent 安全设计文档
- 在 Agent 中加入权限控制层

---

### Day 83 - Day 84：Agent 服务化接入

**学习内容：**

- Agent 封装为异步 API：
  - 提交任务 → 返回 task_id
  - 轮询任务状态：`GET /v1/agent/tasks/{task_id}`
  - 获取结果
- SSE 实时推送 Agent 执行过程
- 任务超时与取消
- 日志回放：通过 trace 重放 Agent 执行过程

**产出物：**
- 将 Agent 封装成 `/v1/agent/run` 接口
- 支持任务提交 → 状态查询 → 结果获取

---

## Phase 6：终极项目 —— 企业级 AI-Gateway（Day 85 - Day 100）

> 目标：万剑归宗。把前面 84 天积累的所有能力，统一接入一个高并发、高可用的企业级模型网关。
>
> 这是你整个 GitHub 仓库最核心的作品集项目。

---

### Day 85 - Day 87：Gateway v0 — 统一模型调用

**功能清单：**

- 统一 `/v1/chat/completions` 接口（兼容 OpenAI 格式）
- 支持多 Provider：
  - 云端：OpenAI、DeepSeek、Qwen、Claude、Gemini
  - 本地：llama.cpp server、Ollama、vLLM、MLX LM
- 统一请求/响应 Schema
- 支持普通输出 + Streaming（SSE）
- 统一错误格式
- 模型列表接口：`GET /v1/models`

**产出物：**
- `gateway_v0/` 目录
- 至少接入 1 个云端模型 + 1 个本地模型

---

### Day 88 - Day 90：Gateway v1 — 模型路由与 Fallback

**功能清单：**

- 模型路由策略：
  - 按任务类型路由（简单任务 → 便宜模型，复杂任务 → 强模型）
  - 按优先级路由（优先本地，超时切云端）
- 失败重试：指数退避、最大重试次数
- Fallback 降级链：
  `local-model → timeout → cheap-cloud-model → error → strong-cloud-model`
- 超时控制：请求级超时 + Token 级超时
- 路由配置化：`fallback_policy.yaml`

**产出物：**
- `router.py`：可配置的模型路由器
- `fallback_policy.yaml`：降级策略配置
- 压测验证 fallback 链生效

---

### Day 91 - Day 92：Gateway v2 — Redis 限流与缓存

**功能清单：**

- API Key 认证：请求头 `Authorization: Bearer sk-xxx`
- Redis 限流：
  - 令牌桶算法（Token Bucket）
  - 用户级限流（每分钟 N 次）
  - IP 级限流
- 请求缓存：相同请求返回缓存结果（节省 Token 成本）
- 会话 Memory：对话上下文存储在 Redis
- API 密钥池轮询：多个 Key 负载均衡
- 熔断机制：某个 Provider 错误率过高时自动熔断

**产出物：**
- `redis_rate_limiter.py`
- `api_key_manager.py`
- `circuit_breaker.py`

---

### Day 93 - Day 94：Gateway v3 — 计费与日志

**功能清单：**

- 结构化请求日志（JSON 格式）：
  - 请求时间、用户、模型、输入 token 数、输出 token 数、延迟
- Token 用量统计：
  - 按用户统计
  - 按模型统计
  - 按日期统计
- 用户额度管理：
  - 每日/每月 Token 配额
  - 配额预警
- 模型成本估算：
  - 不同模型的输入/输出单价
  - 实时计算请求成本
- 异常记录：超时、限流、认证失败、模型错误
- PostgreSQL 持久化存储

**产出物：**
- PostgreSQL 表结构设计
- 调用记录持久化
- 日/周/月用量统计 SQL

---

### Day 95 - Day 96：Gateway v4 — RAG 与 Agent 接入

**功能清单：**

- RAG 查询接口：`POST /v1/rag/query`
  - 知识库选择
  - 检索 + 生成
  - 引用来源返回
- Agent 任务接口：`POST /v1/agent/run`
  - 提交任务 → task_id
  - 任务状态查询：`GET /v1/agent/tasks/{task_id}`
  - 任务结果获取
- 流式 RAG 问答（SSE，每个阶段推送事件）
- Agent 执行过程实时推送

**产出物：**
- Phase 3 的 RAG 模块接入 Gateway
- Phase 5 的 Agent 模块接入 Gateway

---

### Day 97 - Day 98：Dashboard 监控大屏

**功能清单：**

- Vue3 + TypeScript 前端项目搭建
- 核心指标展示：
  - 请求总量（QPS）
  - 错误率（按模型、按错误类型）
  - TTFT（首 Token 响应时间）P50/P95/P99
  - tokens/s（吞吐量）
  - 模型调用分布（饼图）
  - 用户额度使用情况
- 日志实时查看
- API Key 管理界面

**产出物：**
- `gateway-dashboard/` 前端项目
- 后端暴露 `/metrics` 接口供 Dashboard 消费

---

### Day 99：Docker Compose 一键部署

**功能清单：**

- 全套服务容器化：
  - FastAPI Gateway
  - Redis
  - PostgreSQL
  - 向量数据库（Chroma / FAISS）
  - 前端 Dashboard（Nginx 静态服务）
  - 本地模型服务（可选）
- Docker Compose 编排：
  - 服务依赖（depends_on + healthcheck）
  - 网络隔离
  - Volume 持久化
  - .env 注入
- 部署文档

**产出物：**
- `docker-compose.yml`（完整版）
- `.env.example`
- `docs/deploy.md`

---

### Day 100：项目总结与作品集包装

**产出物：**

- README 完整版（中英双语摘要）
- 系统架构图（ASCII 或绘图工具）
- 功能演示 GIF / 录屏
- 性能测试报告
- 学习总结与下一步计划
- Star 引导与分享文案

---

## 建议的 GitHub 仓库目录结构

```
llm-fullstack-roadmap/
│
├── README.md                    # 项目首页（路线图 + 快速开始）
├── LICENSE                      # MIT License
├── .gitignore
├── requirements.txt             # 基础依赖
├── pyproject.toml               # 项目配置
├── docker-compose.yml           # 一键部署
├── .env.example                 # 环境变量模板
│
├── assets/                      # 图片与演示资源
│   ├── roadmap.png              # 路线总览图
│   ├── architecture.png         # AI-Gateway 架构图
│   └── demo.gif                 # 功能演示
│
├── docs/                        # 文档
│   ├── 00_overview.md           # 项目总览
│   ├── 01_environment_setup.md  # 环境搭建指南
│   ├── 02_learning_roadmap.md   # 详细学习路线
│   ├── 03_project_matrix.md     # 9 个项目对比矩阵
│   ├── 04_ai_gateway_design.md  # Gateway 设计文档
│   ├── 05_troubleshooting.md    # 常见问题与解决方案
│   ├── 06_references.md         # 参考资料汇总
│   ├── ai_coding_workflow.md    # AI 编程工作流
│   └── agent_safety.md          # Agent 安全设计
│
├── notebooks/                   # Jupyter Notebooks
│   ├── day01_python_review.ipynb
│   ├── day02_pytorch_review.ipynb
│   ├── day03_transformer_intro.ipynb
│   └── rag_eval_demo.ipynb
│
├── phase0_foundation/           # Phase 0：基建与复习
│   ├── python_review/           # Python 复习脚本
│   ├── pytorch_review/          # PyTorch 复习脚本
│   ├── docker_basics/           # Dockerfile + Compose 示例
│   └── git_github/              # Git 工作流指南
│
├── phase1_prompt_api/           # Phase 1：Prompt + API
│   ├── prompt_cookbook/         # Prompt 模板库
│   ├── llm_client/              # 统一 LLM 客户端
│   ├── fastapi_chat/            # FastAPI 聊天服务
│   └── web_chat_demo/           # 前端聊天 Demo
│
├── phase2_llm_internals/        # Phase 2：LLM 原理
│   ├── notes/
│   │   ├── transformer.md
│   │   ├── attention.md
│   │   ├── rope.md
│   │   ├── kv_cache.md
│   │   ├── moe_intro.md
│   │   └── quantization.md
│   ├── attention_from_scratch/  # 手写 Attention
│   ├── quantization_compare/    # 量化对比实验
│   └── lora_demo/               # LoRA 微调 Demo
│
├── phase3_rag/                  # Phase 3：RAG
│   ├── naive_rag/               # 最简 RAG
│   ├── document_loader/         # 文档解析
│   ├── vector_index/            # 向量索引
│   ├── hybrid_search/           # 混合检索
│   ├── langgraph_rag/           # LangGraph RAG 状态机
│   ├── llamaindex_rag/          # LlamaIndex RAG
│   ├── rag_evaluation/          # RAG 评估
│   └── rag_web_app/             # RAG Web 应用
│
├── phase4_projects/             # Phase 4：9 个项目
│   ├── 01_mlx_lm/
│   │   ├── README.md
│   │   └── mlx_lm_runbook.md
│   ├── 02_llama_cpp/
│   │   ├── README.md
│   │   ├── scripts/
│   │   └── llama_cpp_runbook.md
│   ├── 03_diffusers/
│   │   ├── README.md
│   │   └── diffusers_demo.ipynb
│   ├── 04_sam2/
│   │   ├── README.md
│   │   └── sam2_segmentation_demo.ipynb
│   ├── 05_qwen_vl_llava/
│   │   ├── README.md
│   │   └── vision_llm_demo.md
│   ├── 06_langgraph_rag/
│   │   ├── README.md
│   │   └── langgraph_rag_app/
│   ├── 07_llamaindex/
│   │   ├── README.md
│   │   └── llamaindex_knowledge_base/
│   ├── 08_graphrag/
│   │   ├── README.md
│   │   ├── graphrag_notes.md
│   │   └── graphrag_demo/
│   ├── 09_swe_agent/
│   │   ├── README.md
│   │   ├── code_agent_runbook.md
│   │   └── tasks/
│   └── PROJECTS_SUMMARY.md
│
├── phase5_agent/                # Phase 5：Agent
│   ├── react_agent/             # ReAct Agent
│   ├── langgraph_agent/         # LangGraph 多节点 Agent
│   ├── tool_calling/            # 工具定义与调用
│   └── agent_api/               # Agent 服务化
│
├── final_ai_gateway/            # Phase 6：AI-Gateway
│   ├── README.md
│   ├── backend/
│   │   ├── app.py               # FastAPI 主入口
│   │   ├── router.py            # 模型路由
│   │   ├── providers/           # 各模型 Provider
│   │   ├── rate_limiter.py      # Redis 限流
│   │   ├── api_key_manager.py   # API Key 管理
│   │   ├── circuit_breaker.py   # 熔断器
│   │   ├── billing.py           # 计费模块
│   │   ├── rag_routes.py        # RAG 接口
│   │   ├── agent_routes.py      # Agent 接口
│   │   └── schemas.py           # Pydantic Schema
│   ├── frontend/
│   │   └── gateway-dashboard/   # Vue3 Dashboard
│   ├── configs/
│   │   ├── fallback_policy.yaml
│   │   └── models.yaml
│   ├── scripts/
│   │   ├── seed_db.py
│   │   └── bench_gateway.py
│   ├── tests/
│   │   ├── test_router.py
│   │   ├── test_rate_limiter.py
│   │   └── test_gateway_e2e.py
│   └── docker/
│       ├── Dockerfile.gateway
│       └── nginx.conf
│
└── weekly_logs/                 # 周记（学习过程记录）
    ├── week01.md
    ├── week02.md
    └── ...
```

---

## README 大纲

```markdown
# 100-Day LLM Engineering Roadmap：从本地推理到高并发 AI-Gateway

[![Stars](https://img.shields.io/github/stars/你的用户名/llm-fullstack-roadmap)](https://github.com/你的用户名/llm-fullstack-roadmap)
[![License](https://img.shields.io/github/license/你的用户名/llm-fullstack-roadmap)](./LICENSE)

一个面向本科生的 100 天大模型应用工程学习路线。
从 Python/Prompt/API 入门，到 RAG、Agent、模型微调、多模态，
再到最终自研企业级 AI-Gateway。

## 适合人群

- 有 Python 基础的本科生
- 想入门大模型应用开发的同学
- 不想只停留在调用 API 的学习者
- 想做一个能放进简历和作品集的 AI 工程项目的人

## 路线特色

- **拒绝无脑调包**：深入 Transformer、Attention、KV Cache 底层
- **贴近工业界**：补齐 Docker/Redis/PostgreSQL/Nginx 工程基建
- **1 个月项目冲刺**：复现 9 大主流开源项目
- **工程化大收官**：自研多模型 AI-Gateway，Docker Compose 一键部署

## 你将学到什么

[技能矩阵表]

## 100 天路线总览

[路线表]

## 最终项目：AI-Gateway

[Gateway 介绍]

## 快速开始

```bash
git clone https://github.com/你的用户名/llm-fullstack-roadmap.git
cd llm-fullstack-roadmap
conda create -n llm-roadmap python=3.11
conda activate llm-roadmap
pip install -r requirements.txt
```

## 目录结构

[目录树]

## Star History

[Star 趋势图]

## License

MIT
```

---

## 你现在还缺什么？

对照上面的完整大纲，以下是**你目前内容中还没有覆盖或需要补充的部分**：

### 需要新增的内容

| 缺失项 | 重要性 | 建议 |
|---|---|---|
| **Git/GitHub 工作流** | 高 | Phase 0 Day 1 新增，Conventional Commits、PR 流程 |
| **SSH 配置** | 高 | Phase 0 Day 1 新增，远程开发必备 |
| **Linux 命令深挖** | 高 | Phase 0 Day 4 扩充，进程管理、端口排查、日志 |
| **Nginx 反向代理** | 中 | Phase 6 补充，Gateway 前面挂 Nginx |
| **CI/CD (GitHub Actions)** | 中 | Phase 6 补充，自动测试 + 自动构建镜像 |
| **pytest 测试** | 中 | 贯穿全路线，每个模块都应写测试 |
| **WebSocket vs SSE** | 中 | Phase 1 Day 13 补充对比 |
| **Alembic 数据库迁移** | 中 | Phase 6 补充，PostgreSQL schema 版本管理 |
| **CORS 配置** | 低 | Phase 1 FastAPI 部分补充 |
| **日志系统设计** | 中 | Phase 6 补充，结构化日志、日志级别、轮转 |
| **uv 包管理器** | 低 | Phase 0 Day 4 可选提及 |
| **Prompt Injection 防御** | 中 | Phase 5 已有，可单独成文 |
| **模型评估（Eval）体系** | 中 | Phase 3 已有 RAG 评估，可扩展到通用 |
| **GitHub Profile 优化** | 低 | 最后包装阶段 |

### 需要细化的内容

| 现有内容 | 问题 | 建议 |
|---|---|---|
| Phase 0 Day 2 Python 复习 | 只有基础语法 | 加入异步编程 (asyncio)、类型注解深入 |
| Phase 0 Day 5 Docker | 只提到入门 | 加入多阶段构建、healthcheck、网络类型 |
| Phase 1 Prompt | 只有基础 CoT | 加入 Self-Consistency、Reflexion、结构化 JSON |
| Phase 2 LoRA | 只有概念 | 加入 LoRA 数学、rank 选择策略、数据配比 |
| Phase 4 项目 | 原来每项目一周 | 已压缩到 2-4 天，每个项目只抓核心 |
| AI-Gateway | 只有架构 | 补充了 v0→v4 迭代路线，每个版本有明确产出 |

### 建议的优先级

1. **先补齐 Phase 0 基建**（Git、SSH、Linux、Docker 深挖）— 这是你目前大纲中最薄弱的
2. **Phase 1 Prompt 强化** — 加入更多高级技巧
3. **Phase 6 Gateway 细化** — 这是你的作品集核心，必须完整可运行
4. **写好 README 和架构图** — 这是别人看到你仓库的第一印象

---

## 关于 9 个项目的 1 个月时间分析

你的分析是对的，9 个项目确实不需要 9 周。以下是压缩后的时间分配逻辑：

```
P1 MLX LM:        2 天 — 最轻量，Mac 用户跑通即可
P2 llama.cpp:     3 天 — 需要压测，所以多 1 天
P3 Diffusers:     3 天 — 三个任务 (txt2img/img2img/inpaint)
P4 SAM 2:         3 天 — 需要理解 mask 工程
P5 Qwen-VL/LLaVA: 4 天 — 两个模型 + 多任务
P6 LangGraph:     4 天 — 代码量大，核心项目
P7 LlamaIndex:    3 天 — 对比学习，基于 P6 经验会更快
P8 GraphRAG:      4 天 — 概念新，构建图谱耗时
P9 SWE-agent:     4 天 — 需要准备 repo 和 issue

总计 30 天 ≈ 1 个月
```

**前提条件**：Phase 0-3 的基础已经打好（Python、LLM 原理、RAG 基础），否则每个项目都会卡在环境配置上。

---

## 最终建议

1. **README 是第一印象**：架构图 + 路线图 + 技能矩阵 + 快速开始，四个缺一不可
2. **AI-Gateway 是作品集核心**：前面的 Prompt、RAG、Agent、Docker、Redis、FastAPI 都服务于这个终局
3. **不要追求每个项目都完美**：9 个项目只需要最小可运行 Demo + 避坑记录 + 可复用模块
4. **写周记**：`weekly_logs/` 每周一篇，记录学到什么、踩了什么坑，这是面试时最好的素材
5. **让你的学弟学妹能跑通**：`docs/01_environment_setup.md` 和 `docs/05_troubleshooting.md` 写详细，这是 Star 的来源
