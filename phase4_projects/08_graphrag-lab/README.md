# P8: GraphRAG Lab — 知识图谱检索实验平台

> 一套生产级 GraphRAG 实验平台，完整实现 Microsoft GraphRAG 流水线，并与传统 Vector RAG 进行端到端对比基准测试 —— 全部在 MacBook 本地运行，嵌入向量零 API 成本。

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](./LICENSE)
[![Platform: macOS](https://img.shields.io/badge/platform-macOS%20Apple%20Silicon-silver)](https://www.apple.com/mac/)

---

## 项目概述

GraphRAG 是微软提出的检索增强生成方法：它从文档中构建**知识图谱**——提取实体、关系、层次化社区结构——然后通过遍历这张结构化表示来回答查询，而非简单的向量相似度匹配。

本项目提供了一套完整可运行的实现，帮助你：

- **端到端运行**完整 GraphRAG 流水线（实体提取 → 关系提取 → Leiden 社区检测 → 社区摘要 → 查询回答）
- 在 **Global Search**（社区级主题回答）和 **Local Search**（实体中心式遍历）之间切换
- **横向对比** GraphRAG 与 Vector RAG 基线（Chroma + BGE-M3）
- 一切**本地运行、低成本**：嵌入向量在 Apple Metal/MPS 上本地计算，零 API 费用；仅 LLM 推理调用 DeepSeek API

### GraphRAG vs Vector RAG 适用场景

| 能力 | GraphRAG | Vector RAG |
|:---|---:|:---|
| 多跳推理（"A、B、C 之间有什么关系？"） | | |
| 全局主题摘要 | | |
| 实体关系查询 | | |
| 事实查找（"X 是什么？"） | | |
| 关键词搜索 | | |
| 查询延迟 | 3-10s | 0.3-1s |
| 索引时间 | 5-10 分钟（含 LLM） | 1-2 分钟 |

---

## 系统架构

```
data/raw/*.txt（52 篇 AI/ML 维基百科 + arXiv 文章）
        │
        ▼
[文档预处理]
  清洗、标准化、过滤短于 200 字的文档
        │
        ▼
data/input/*.txt
        │
        ▼
[GraphRAG 索引流水线]                         [嵌入向量服务]
  ├─ 文本分块                                    BGE-M3 模型
  ├─ 实体提取（DeepSeek API）                     Metal/MPS 加速
  ├─ 关系提取（DeepSeek API）                     :19530（OpenAI 兼容接口）
  ├─ Leiden 社区检测                              零 API 费用
  ├─ 社区摘要（DeepSeek API）
  └─ 文本嵌入向量 ←─────────────────────────────────┤
        │
        ▼
data/output/*.parquet（实体、关系、社区、社区报告）
        │
        ├──▶ Global Search  — 基于社区报告的 map-reduce 全局回答
        └──▶ Local Search   — 基于实体邻域展开的局部回答

Vector RAG 基线：
data/input/*.txt → 文本分块 → BGE-M3 向量化 → Chroma → 余弦相似度检索
```

### 设计选型

| 决策 | 理由 |
|:-----|:-----|
| **DeepSeek 驱动 LLM** | 国内无需 VPN 即可访问，支持实体提取所需的 JSON Mode，约 ¥1/M tokens |
| **BGE-M3 本地嵌入** | 索引过程中调用量最大的环节（每次 200-400 次），MPS 本地运行消除成本 |
| **独立的嵌入服务** | GraphRAG 期望 OpenAI 兼容的 API 接口；FastAPI 适配器桥接 BGE-M3 |
| **Chroma 做 Vector RAG** | 轻量、持久化、无外部依赖，使用相同嵌入模型保证对比公平 |

---

## 快速开始

### 前置条件

- macOS + Apple Silicon（M1 及以上）
- [Miniforge](https://github.com/conda-forge/miniforge)（Conda 环境管理）
- [DeepSeek API Key](https://platform.deepseek.com/api_keys)（免费额度足够使用）

### 一键配置环境

```bash
# 1. 创建 conda 环境 + 安装全部依赖 + 预热 BGE-M3 模型
make setup

# 2. 下载 AI/ML 语料库（50+ 篇维基百科文章）
make download-corpus
make preprocess

# 3. 配置 API Key
cp .env.example .env
# 编辑 .env → 设置 GRAPHRAG_API_KEY=sk-你的deepseek密钥

# 4. 初始化 GraphRAG 项目
make init-graphrag
```

### 构建索引与查询

```bash
# 终端 1：启动 BGE-M3 嵌入向量服务（保持运行）
make run-embed

# 终端 2：运行完整索引流水线（约 5-10 分钟）
make run-index

# 开始查询！
make run-query-global    # 全局搜索
make run-query-local     # 局部搜索

# 与 Vector RAG 横向对比
make run-vector-rag
make compare

# 分析索引产物
make analyze
```

也可以使用 tmux 一键启动全部服务：

```bash
make run-all    # 启动嵌入 + 索引 + 查询三个窗口
make attach     # 接入 tmux 会话
make stop       # 停止全部服务
```

---

## 项目结构

```
08_graphrag-lab/
├── Makefile                      # 一键编排所有命令
├── pyproject.toml                # 包元数据与构建配置
├── requirements.txt              # Python 依赖清单
├── .env.example                  # 环境变量模板
├── runbook.md                    # 详细排错手册
│
├── configs/
│   ├── settings.yaml             # 主配置：DeepSeek API + 本地嵌入
│   └── settings.local.yaml       # 备选配置：llama.cpp 纯本地模式
│
├── data/
│   ├── raw/                      # 原始维基百科语料（52 个主题）
│   ├── input/                    # 预处理后的 .txt 文件，供索引用
│   ├── output/                   # GraphRAG 索引产物（*.parquet）
│   └── vector_store/             # Chroma 向量数据库
│
├── src/graphrag_lab/
│   ├── serve_embedding.py        # BGE-M3 嵌入 API 服务（FastAPI）
│   ├── corpus.py                 # 语料下载与管理
│   ├── querier.py                # GraphRAG 查询接口
│   └── comparator.py             # GraphRAG vs Vector RAG 对比引擎
│
├── scripts/
│   ├── 00_check_env.py           # 环境检查
│   ├── 01_download_corpus.sh     # 语料下载脚本
│   ├── 02_preprocess_docs.py     # 文档清洗与标准化
│   ├── 03_init_graphrag.py       # GraphRAG 项目初始化
│   ├── 04_query_demo.py          # 查询演示（Global + Local）
│   ├── 05_vector_rag_baseline.py # Vector RAG 基线构建
│   ├── 06_compare_rag.py         # 横向对比基准测试
│   └── 07_analyze_artifacts.py   # Parquet 产物分析器
│
├── prompts/
│   ├── entity_extraction.txt     # 自定义实体提取提示词
│   └── community_report.txt      # 自定义社区摘要提示词
│
├── tests/
│   ├── test_comparator.py        # 对比器单元测试
│   └── __init__.py
│
└── docs/
    ├── architecture.md           # 系统架构与数据流设计
    └── comparison_report.md      # 自动生成的对比测试报告
```

---

## 配置说明

### 环境变量

| 变量 | 必填 | 用途 |
|:-----|:---:|:-----|
| `GRAPHRAG_API_KEY` | 是 | DeepSeek API 密钥 |
| `GRAPHRAG_EMBEDDING_API_BASE` | 是 | 本地嵌入服务地址 |
| `GRAPHRAG_EMBEDDING_API_KEY` | 是 | 嵌入服务认证（设为 `local`） |
| `GRAPHRAG_EMBEDDING_MODEL` | 是 | 嵌入模型名称（默认 `bge-m3`） |
| `HF_ENDPOINT` | 国内 | HuggingFace 镜像站 |
| `NO_PROXY` | 国内 | 本地服务绕过代理 |

### GraphRAG 设置文件

| 文件 | 使用场景 |
|:-----|:--------|
| `configs/settings.yaml` | **默认** — DeepSeek API 做 LLM + 本地 BGE-M3 做嵌入 |
| `configs/settings.local.yaml` | **备选** — llama.cpp 纯本地模式（监听 :8081） |

---

## API 参考

### Python 包

```python
from graphrag_lab import CorpusDownloader, GraphRAGQuerier, RAGComparator

# 下载与管理语料
corpus = CorpusDownloader(output_dir="data/raw")
corpus.download_wikipedia("Knowledge_graph", language="en")

# 查询 GraphRAG
querier = GraphRAGQuerier(root_dir=".", method="global")
result = querier.ask("这些文档主要讨论了哪些主题？")

# 对比 GraphRAG 与 Vector RAG
comparator = RAGComparator(
    graphrag_root=".",
    vector_store="data/vector_store",
    embedding_model="BAAI/bge-m3"
)
report = comparator.compare(["什么是迁移学习？", "注意力机制如何工作？"])
```

### 命令行

```bash
# 查询演示
python scripts/04_query_demo.py --method global --query "解释 Transformer 架构"

# 构建 Vector RAG 基线
python scripts/05_vector_rag_baseline.py --input data/input --embedding-model BAAI/bge-m3

# 运行对比基准测试
python scripts/06_compare_rag.py --output docs/comparison_report.md

# 分析索引产物
python scripts/07_analyze_artifacts.py
```

---

## 性能基准

基于 52 篇 AI/ML 语料的实测结果（MacBook Pro M5, 24GB 内存）：

| 指标 | GraphRAG Global | GraphRAG Local | Vector RAG |
|:---|---:|---:|---:|
| 查询延迟 | 5-10s | 3-6s | 0.3-1s |
| 索引时间 | 8 分钟 | — | 1.5 分钟 |
| 嵌入成本 | ¥0 | ¥0 | ¥0 |
| LLM API 成本 | ~¥0.35/次 | ~¥0.21/次 | ~¥0.07/次 |
| 多跳推理准确率 | 高 | 中高 | 低 |
| 事实精度 | 中 | 高 | 极高 |

---

## 常见问题

详见 [runbook.md](./runbook.md)，涵盖：
- Conda 环境配置问题
- HuggingFace 模型下载失败（国内网络）
- 嵌入服务连接错误
- GraphRAG 索引流水线失败
- MPS/GPU 内存管理

快速诊断：

```bash
make check-env                         # 验证运行环境
curl -s http://127.0.0.1:19530/health  # 检查嵌入服务状态
```

---

## 许可证

MIT © Chenxi
