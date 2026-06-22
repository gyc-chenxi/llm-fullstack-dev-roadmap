# P7: LlamaIndex 知识库应用

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

基于 LlamaIndex 构建的**企业级 RAG 知识库系统**，支持语义向量检索、全文树状总结、多知识库 LLM 自动路由，具备完整的摄取管道、持久化存储与 Makefile 自动化。

> 目标硬件：MacBook Air M5 / 32GB Unified Memory / Apple Silicon MPS
>
> 核心价值：掌握 LlamaIndex 核心抽象（Document → Node → Index → QueryEngine）

---

## 架构图

```
Raw Documents (.md / .pdf / .txt)
        ↓
 IngestionPipeline (分块 → 元数据抽取 → BGE 嵌入)
        ↓
 VectorStoreIndex ←→ ChromaDB（持久化向量库）
 SummaryIndex（全文树状索引）
        ↓
 RouterQueryEngine（LLM 驱动的多知识库自动路由）
        ↓
 Vector Query / Summary Query / Multi-KB Route
```

---

## 核心特性

| 特性 | 说明 |
|------|------|
| **VectorStoreIndex** | 语义向量检索 + ChromaDB 持久化，支持 Top-K 相似文档召回 |
| **SummaryIndex** | 全文树状聚合总结，适合"这份文档讲了什么"类问题 |
| **RouterQueryEngine** | LLM 驱动的多知识库自动路由，根据问题类型选择最佳索引 |
| **IngestionPipeline** | 文档分块 → 元数据抽取 → BGE 嵌入，一站式摄取 |
| **多文档加载器** | 支持本地 Markdown、PDF、TXT，预留 Notion/GitHub 连接器 |
| **MPS 加速** | Apple Silicon Metal Performance Shaders 本地推理 |
| **HF 镜像** | 国内 hf-mirror.com 免代理下载 |
| **tmux 多终端** | 一键启动构建 + 查询 + 路由 + 监控面板 |

---

## 环境要求

| 组件 | 要求 |
|------|------|
| OS | macOS (Apple Silicon) / Linux |
| Python | 3.11+ |
| Conda | Miniconda / Anaconda (env: `cxllm`) |
| RAM | 16GB+ (32GB 推荐) |
| Disk | 5GB+ (模型 + 向量库) |

---

## 快速开始（5 分钟）

```bash
# 1. 进入项目
cd 07_llamaindex-knowledge-base-lab

# 2. 一键初始化环境
make setup

# 3. 下载 Embedding 模型
make download

# 4. 放入文档到 data/raw/，然后构建索引
make build

# 5. 启动交互式查询
make query
```

---

## 查询模式

### 向量检索查询

```bash
make query
# 进入交互式 REPL，输入问题进行语义检索
# > 什么是 RoPE 位置编码？
```

### 全文总结查询

```bash
make summary
# 对索引中的全部文档进行树状聚合总结
# > 这些文档共同讨论了哪些主题？
```

### 多知识库路由

```bash
make router
# LLM 自动判断问题类型，路由到最合适的索引
# > 论文 A 和论文 B 在方法上有什么区别？
```

---

## Makefile 命令

| 命令 | 说明 |
|------|------|
| `make setup` | 一键初始化环境 + 安装依赖 |
| `make download` | 下载 BGE-Small-ZH 嵌入模型 |
| `make build` | 构建 VectorStoreIndex 索引 |
| `make build-summary` | 构建 SummaryIndex 索引 |
| `make query` | 启动交互式向量检索查询 |
| `make summary` | 启动 SummaryIndex 全文总结查询 |
| `make router` | 启动 RouterQueryEngine 多知识库路由 |
| `make run-all` | 后台启动全部服务 (nohup) |
| `make run-all-tmux` | tmux 一键启动全部服务面板 |
| `make test` | 运行全部单元测试 |
| `make lint` | 代码质量检查 (ruff) |
| `make status` | 查看运行状态 (进程 + 内存 + 端口) |
| `make logs` | 实时查看应用日志 |
| `make kill` | 停止所有后台 Python 进程 |
| `make clean` | 清理缓存和构建产物 |
| `make clean-all` | 深度清理（包括模型文件） |

---

## 项目结构

```
07_llamaindex-knowledge-base-lab/
├── Makefile                       # 一键自动化入口
├── requirements.txt               # Python 依赖清单
├── .gitignore / .gitattributes
│
├── configs/
│   ├── settings.yaml              # 运行时主配置
│   └── model_config.yaml          # Embedding / LLM 模型参数
│
├── data/
│   ├── raw/                       # 原始文档（只读不写）
│   │   ├── notes/                 #   学习笔记
│   │   └── papers/                #   论文总结
│   ├── processed/                 # 清洗/分块后的中间产物
│   └── vector_store/              # ChromaDB 持久化向量库
│
├── models/
│   └── bge-small-zh-v1.5/         # BGE 中文嵌入模型
│
├── src/
│   ├── loaders/                   # 文档加载器（本地/Notion/GitHub 连接器）
│   │   └── document_loader.py
│   ├── ingestion/                 # 摄取管道（分块 + 元数据抽取）
│   │   └── pipeline.py
│   ├── indexes/                   # 索引构建（Vector / Summary）
│   │   ├── build_vector_index.py
│   │   └── build_summary_index.py
│   ├── query_engines/             # 查询引擎封装
│   │   ├── base.py
│   │   ├── vector_query.py
│   │   └── summary_query.py
│   ├── routers/                   # 多知识库路由器
│   │   └── multi_kb_router.py
│   └── utils/                     # 工具函数（配置/设备检测/LLM 封装）
│       ├── config.py
│       ├── device.py
│       └── deepseek_llm.py
│
├── scripts/                       # Shell 自动化脚本
│   ├── setup_env.sh
│   ├── download_models.sh
│   ├── ingest.sh
│   └── query.sh
│
├── tests/                         # 单元测试
│   ├── test_ingestion.py
│   ├── test_indexes.py
│   └── test_router.py
│
├── storage/                       # LlamaIndex 索引持久化
├── logs/                          # 运行时日志
├── docs/                          # 架构文档 & 对比报告
└── runbook.md                     # 完整操作手册
```

---

## 技术栈

| 层级 | 技术 |
|------|------|
| RAG 框架 | LlamaIndex 0.12+ |
| 向量数据库 | ChromaDB (PersistentClient) |
| Embedding | BAAI/bge-small-zh-v1.5（SentenceTransformers，中文优化） |
| LLM | GPT-4o-mini（通过 OpenAI API）/ DeepSeek |
| 设备加速 | Apple Silicon MPS (Metal Performance Shaders) |
| 配置管理 | YAML |
| 环境管理 | Conda + Python 3.11 |
| 测试 | pytest |
| 代码质量 | ruff |

---

## 常见问题

<details>
<summary><b>ChromaDB 向量库损坏或查询异常？</b></summary>

```bash
make clean      # 清理向量库和缓存
make build      # 重新构建索引
```
</details>

<details>
<summary><b>模型下载慢或失败？</b></summary>

项目已配置 `HF_ENDPOINT=https://hf-mirror.com`（国内镜像），自动走镜像下载。
</details>

<details>
<summary><b>MPS 不可用？</b></summary>

```bash
# 检查 MPS 状态
python -c "import torch; print(torch.backends.mps.is_available())"
# 如返回 False，自动回退到 CPU
```
</details>

---

## 项目价值表达（简历用）

> 基于 LlamaIndex 构建企业级 RAG 知识库系统，设计 VectorStoreIndex / SummaryIndex / RouterQueryEngine 三种查询模式；实现 IngestionPipeline 文档摄取流水线（分块 → 元数据抽取 → BGE 嵌入），集成 ChromaDB 持久化向量存储与 LLM 驱动的多知识库自动路由；在 Apple Silicon 本地环境下完成从文档加载、索引构建到交互式查询的全流程工程化落地。

---

## 许可证

MIT
