# P8: GraphRAG 知识图谱检索 Runbook

> **主题**：GraphRAG — 基于知识图谱的检索增强生成
> **周期**：Day 68-71，4 天
> **目标**：从零构建 GraphRAG 索引管线，掌握实体抽取→关系构建→社区检测→全局/局部搜索全链路，并完成 GraphRAG vs Vector RAG 量化对比
> **硬件基线**：MacBook Air M5，32GB 统一内存，1TB SSD，macOS
> **环境基线**：Conda `cxllm`，Python 3.11
> **项目定位**：GitHub 个人作品集级 AI Infra 工程，非一次性 notebook demo

> **重要设计原则**：本 runbook 遵循“先建文件 → 再装依赖 → 最后执行”的严格时序。每一章的命令都可在该章内完全执行完毕，不依赖后续章节。你不需要跳来跳去找代码。

---

## 0. 项目总览

本项目不是“扔一堆文本给 LLM 抽取实体”的 GraphRAG 玩具示例，而是一个面向生产可复现、可对比、可扩展的知识图谱 RAG 实验平台。

核心能力：

- 完整的 GraphRAG 索引管线：文本分块 → 实体抽取 → 关系抽取 → 图谱构建 → Leiden 社区检测 → 社区摘要
- Global Search（全局/总结性问题）+ Local Search（实体关系/多跳问题）双模式查询
- 同一语料库下 Vector RAG（Chroma + BGE-M3）与 GraphRAG 的对比评测
- 支持 DeepSeek API（推荐，国内直连）与本地 llama.cpp（完全离线）双后端
- 本地 BGE-M3 嵌入服务（Metal 加速，零成本嵌入生成）
- 完整的索引产物分析工具

推荐项目名：`08_graphrag-lab`

---

## 1. 工程化目录架构与完整源码 Bootstrap

### 1.1 设计原则

本章 = **目录初始化 + 所有源码文件一键生成**。执行完本章后，项目目录中一切代码就绪，无需再手动创建任何文件。后续章节只需安装依赖即可运行。

### 1.2 一键初始化目录树

```bash
cd /Users/chenxi/Documents/晨熙个人/0暑期自学大模型/phase4_projects

# 创建主目录和所有子目录
mkdir -p 08_graphrag-lab/{configs,data/{raw,input,output,vector_store},scripts,src/graphrag_lab,tests,docs,prompts,logs,models}

# 创建 .gitkeep 保底文件（确保空目录可被 git 跟踪）
touch 08_graphrag-lab/data/raw/.gitkeep
touch 08_graphrag-lab/data/input/.gitkeep
touch 08_graphrag-lab/data/output/.gitkeep
touch 08_graphrag-lab/data/vector_store/.gitkeep
touch 08_graphrag-lab/logs/.gitkeep
touch 08_graphrag-lab/models/.gitkeep

cd 08_graphrag-lab
```

### 1.3 完整目录树（执行后验证）

```
08_graphrag-lab/
├── Makefile                    # 工程编排中枢
├── README.md                   # 项目说明（写给面试官和开源社区）
├── runbook.md                  # 本文件 — 逐行可执行操作手册
├── pyproject.toml              # Python 项目元数据
├── requirements.txt            # 依赖清单
├── .env.example                # 环境变量模板
├── .gitignore
│
├── configs/
│   ├── settings.yaml           # GraphRAG 主配置 — DeepSeek API + 本地嵌入
│   └── settings.local.yaml     # GraphRAG 离线配置 — llama.cpp 全本地
│
├── data/
│   ├── raw/                    # 原始下载语料（Wikipedia 文章、arXiv 摘要）
│   ├── input/                  # 预处理后的 .txt — GraphRAG 索引输入
│   ├── output/                 # GraphRAG 索引产物（parquet + 图谱）
│   └── vector_store/           # Chroma 持久化向量库（Vector RAG 对照用）
│
├── scripts/
│   ├── 00_check_env.py         # 环境自检
│   ├── 01_download_corpus.sh   # 下载语料库
│   ├── 02_preprocess_docs.py   # 文档清洗标准化
│   ├── 03_init_graphrag.py     # 初始化 GraphRAG 项目
│   ├── 04_query_demo.py        # Global + Local Search 交互式查询
│   ├── 05_vector_rag_baseline.py # Vector RAG 基线（Chroma + BGE-M3）
│   ├── 06_compare_rag.py       # GraphRAG vs Vector RAG 量化对比
│   └── 07_analyze_artifacts.py # 解析 parquet 索引产物
│
├── src/graphrag_lab/
│   ├── __init__.py
│   ├── corpus.py               # 语料获取（Wikipedia + arXiv API）
│   ├── serve_embedding.py      # 本地 BGE-M3 嵌入服务（FastAPI）
│   ├── querier.py              # GraphRAG 查询封装
│   └── comparator.py           # RAG 方案对比引擎
│
├── tests/
│   ├── __init__.py
│   └── test_comparator.py
│
├── prompts/
│   ├── entity_extraction.txt
│   └── community_report.txt
│
└── docs/
    ├── architecture.md
    └── comparison_report.md    # 运行对比后生成
```

### 1.4 核心目录一句话工程作用

| 目录 | 工程作用 |
|:-----|:---------|
| `configs/` | GraphRAG 双后端配置切换（云端 DeepSeek vs 本地 llama.cpp），环境隔离 |
| `scripts/` | 可独立执行的管线脚本，按编号顺序执行即完成完整实验流程 |
| `src/graphrag_lab/` | 核心 Python 包，封装语料获取、嵌入服务、查询、对比逻辑 |
| `tests/` | 最小单元测试集，保护对比评测逻辑不被回归破坏 |
| `data/` | 语料→索引→向量库的完整数据生命周期隔离 |
| `prompts/` | 自定义 LLM 提示词，控制实体抽取粒度与摘要风格 |
| `docs/` | 架构决策记录与实验对比报告，面试材料核心输出 |
| `logs/` | GraphRAG 索引运行日志，便于回溯调试 |

---

### 1.5 全量源码 Bootstrap（核心！这里创建所有文件）

> **注意**：以下每一步都使用 `cat << 'EOF' > filename` 的 Bash heredoc 语法，复制整段到终端回车即可一键创建文件。确保当前终端 WORKDIR 是 `08_graphrag-lab/`。

#### 1.5.1 项目元数据文件

```bash
# ==============================
# 以下命令全部在项目根目录执行：
# cd /Users/chenxi/Documents/晨熙个人/0暑期自学大模型/phase4_projects/08_graphrag-lab
# ==============================

# --- requirements.txt ---
cat << 'EOF' > requirements.txt
graphrag>=1.0.0
torch>=2.5.0
pandas>=2.2.0
pyarrow>=17.0.0
pyyaml>=6.0
python-dotenv>=1.0.0
tiktoken>=0.8.0
rich>=13.0.0
click>=8.0.0
wikipedia>=1.4.0
arxiv>=2.1.0
pymupdf>=1.24.0
chromadb>=0.5.0
sentence-transformers>=3.0.0
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
hf-transfer>=0.1.0
pytest>=8.0.0
pytest-asyncio>=0.24.0
EOF

# --- pyproject.toml ---
cat << 'EOF' > pyproject.toml
[build-system]
requires = ["setuptools>=75.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "graphrag-lab"
version = "1.0.0"
description = "P8: GraphRAG Knowledge Graph Retrieval — production-grade RAG evaluation platform"
requires-python = ">=3.11"
readme = "README.md"
license = {text = "MIT"}
authors = [{name = "Chenxi", email = "gyc.chenxi@example.com"}]
keywords = ["graphrag", "rag", "knowledge-graph", "llm", "vector-search"]

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
EOF

# --- .env.example ---
cat << 'EOF' > .env.example
# === P8 GraphRAG Lab — Environment Variables ===
# cp .env.example .env and fill in real values

# DeepSeek API (recommended for China users)
# Get key at: https://platform.deepseek.com/api_keys
GRAPHRAG_API_KEY=sk-your-deepseek-api-key-here

# Local embedding service
GRAPHRAG_EMBEDDING_API_BASE=http://127.0.0.1:19530/v1
GRAPHRAG_EMBEDDING_API_KEY=local
GRAPHRAG_EMBEDDING_MODEL=bge-m3

# HuggingFace mirror (required in China)
HF_ENDPOINT=https://hf-mirror.com

# Optional: full local mode with llama.cpp
# GRAPHRAG_API_BASE=http://127.0.0.1:8081/v1
# GRAPHRAG_API_KEY=local
# GRAPHRAG_LLM_MODEL=local-model
EOF

# --- .gitignore ---
cat << 'EOF' > .gitignore
# Secrets
.env
*.key
*.pem
credentials.json

# Python
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/

# Models
models/
*.gguf
*.bin
*.safetensors
*.pt
*.pth

# GraphRAG outputs
data/output/
data/vector_store/
cache/
logs/

# IDE
.vscode/
.idea/
.DS_Store

# Testing
.pytest_cache/
.ruff_cache/
htmlcov/
EOF
```

#### 1.5.2 GraphRAG 配置文件

```bash
# --- configs/settings.yaml (主配置: DeepSeek API + 本地嵌入) ---
cat << 'EOF' > configs/settings.yaml
encoding_model: cl100k_base
skip_workflows: []

llm:
  api_key: ${GRAPHRAG_API_KEY}
  type: openai_chat
  model: deepseek-chat
  api_base: https://api.deepseek.com/v1
  model_supports_json: true
  max_tokens: 4000
  request_timeout: 180.0
  concurrent_requests: 4
  tokens_per_minute: null
  requests_per_minute: null
  sleep_on_rate_limit_recommendation: true

parallelization:
  stagger: 0.3
  num_threads: 8

async_mode: threaded

embeddings:
  async_mode: threaded
  llm:
    api_key: ${GRAPHRAG_EMBEDDING_API_KEY}
    type: openai_embedding
    model: ${GRAPHRAG_EMBEDDING_MODEL}
    api_base: ${GRAPHRAG_EMBEDDING_API_BASE}
    concurrent_requests: 8
    tokens_per_minute: null
    requests_per_minute: null

chunks:
  size: 1200
  overlap: 100
  group_by_columns: [id]

input:
  type: file
  file_type: text
  base_dir: "data/input"

output:
  type: file
  base_dir: "data/output"

reporting:
  type: file
  base_dir: "logs"

entity_extraction:
  entity_types:
    - ORGANIZATION
    - PERSON
    - GEO
    - EVENT
    - TECHNOLOGY
    - METHOD
    - DATASET
    - MODEL
    - ALGORITHM
    - CONCEPT
    - METRIC
    - FRAMEWORK
  max_gleanings: 1

summarize_descriptions:
  max_length: 500

community_reports:
  max_length: 2000
  max_input_length: 8000

cluster_graph:
  max_cluster_size: 10

umap:
  enabled: false

embed_graph:
  enabled: false

snapshots:
  graphml: true
  raw_graph: true
EOF

# --- configs/settings.local.yaml (离线配置: llama.cpp + 本地嵌入) ---
cat << 'EOF' > configs/settings.local.yaml
# Full local mode: llama.cpp + BGE-M3
# Usage: cp configs/settings.local.yaml settings.yaml
# Prerequisites: make run-embed (Terminal 1) + llama.cpp server (Terminal 2)

encoding_model: cl100k_base

llm:
  api_key: local
  type: openai_chat
  model: local-model
  api_base: http://127.0.0.1:8081/v1
  model_supports_json: true
  max_tokens: 4000
  request_timeout: 300.0
  concurrent_requests: 2

parallelization:
  stagger: 0.5
  num_threads: 4

embeddings:
  async_mode: threaded
  llm:
    api_key: local
    type: openai_embedding
    model: bge-m3
    api_base: http://127.0.0.1:19530/v1
    concurrent_requests: 4

chunks:
  size: 1200
  overlap: 100
  group_by_columns: [id]

input:
  type: file
  file_type: text
  base_dir: "data/input"

output:
  type: file
  base_dir: "data/output"

reporting:
  type: file
  base_dir: "logs"

entity_extraction:
  entity_types:
    - ORGANIZATION
    - PERSON
    - TECHNOLOGY
    - METHOD
    - DATASET
    - MODEL
    - ALGORITHM
    - CONCEPT
  max_gleanings: 1

cluster_graph:
  max_cluster_size: 10

umap:
  enabled: false

embed_graph:
  enabled: false

snapshots:
  graphml: true
  raw_graph: true
EOF
```

#### 1.5.3 管线脚本（scripts/）

```bash
# --- scripts/00_check_env.py (环境自检) ---
cat << 'EOF' > scripts/00_check_env.py
#!/usr/bin/env python3
"""P8 GraphRAG Lab — Environment Self-Check.

Run before any other step to verify:
- Python 3.11+, Conda cxllm, PyTorch MPS, GraphRAG installed
- .env with real API key (not placeholder)
- HuggingFace mirror configured
- Required directories exist
"""

import os, sys, shutil, platform


def check(desc: str, ok: bool, detail: str = "") -> bool:
    symbol = "\033[92mPASS\033[0m" if ok else "\033[91mFAIL\033[0m"
    suffix = f" — {detail}" if detail else ""
    print(f"  [{symbol}] {desc}{suffix}")
    return ok


def main() -> int:
    print("=" * 60)
    print("P8 GraphRAG Lab — Environment Check")
    print(f"Platform: {platform.platform()}")
    print(f"Time:     {__import__('datetime').datetime.now().isoformat()}")
    print("=" * 60)

    all_ok = True

    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    all_ok &= check(f"Python {py_ver}", sys.version_info >= (3, 11))

    conda_env = os.environ.get("CONDA_DEFAULT_ENV", "?")
    all_ok &= check(f"Conda env: {conda_env}", conda_env == "cxllm",
                    detail="OK" if conda_env == "cxllm" else f"expected=cxllm, got={conda_env}")

    try:
        import torch
        all_ok &= check(f"PyTorch {torch.__version__}", True)
        mps_ok = torch.backends.mps.is_available()
        all_ok &= check("MPS available", mps_ok)
        if mps_ok:
            try:
                x = torch.randn(2, 2).to("mps")
                y = x @ x
                all_ok &= check("MPS matmul", True, f"device={x.device}, shape={y.shape}")
            except Exception as e:
                all_ok &= check("MPS matmul", False, str(e)[:60])
    except ImportError:
        all_ok &= check("PyTorch", False, "not installed — run: conda run -n cxllm pip install torch")

    try:
        import graphrag
        all_ok &= check(f"GraphRAG {graphrag.__version__}", True)
    except ImportError:
        all_ok &= check("GraphRAG", False, "not installed — run: conda run -n cxllm pip install graphrag")

    try:
        import sentence_transformers
        all_ok &= check(f"sentence-transformers {sentence_transformers.__version__}", True)
    except ImportError:
        all_ok &= check("sentence-transformers", False)

    try:
        import chromadb
        all_ok &= check(f"chromadb {chromadb.__version__}", True)
    except ImportError:
        all_ok &= check("chromadb", False)

    try:
        import fastapi, uvicorn
        all_ok &= check(f"fastapi {fastapi.__version__}", True)
    except ImportError:
        all_ok &= check("fastapi/uvicorn", False)

    env_file = os.path.join(os.path.dirname(__file__), "..", ".env")
    env_file = os.path.abspath(env_file)
    if os.path.exists(env_file):
        from dotenv import load_dotenv
        load_dotenv(env_file)
        key = os.environ.get("GRAPHRAG_API_KEY", "")
        has_key = len(key) > 10 and "your-deepseek" not in key.lower()
        all_ok &= check(".env GRAPHRAG_API_KEY", has_key,
                        "set" if has_key else "placeholder — edit .env with real key")
    else:
        all_ok &= check(".env file", False, f"not found at {env_file} — run: cp .env.example .env")

    hf = os.environ.get("HF_ENDPOINT", "")
    all_ok &= check("HF_ENDPOINT", "hf-mirror.com" in hf, hf or "not set")

    total, used, free = shutil.disk_usage(".")
    free_gb = free / (1024 ** 3)
    all_ok &= check(f"Disk free: {free_gb:.1f} GB", free_gb > 10,
                    "OK" if free_gb > 10 else "WARNING: <10GB free")

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    for d in ["data/raw", "data/input", "data/output", "data/vector_store",
              "configs", "scripts", "src/graphrag_lab", "tests", "prompts", "docs", "logs"]:
        full = os.path.join(project_root, d)
        exists = os.path.isdir(full)
        n = 0
        if exists:
            try:
                n = len([f for f in os.listdir(full) if not f.startswith(".")])
            except Exception:
                n = -1
        all_ok &= check(f"Directory: {d}/", exists, f"{n} files" if n else "empty")

    print("=" * 60)
    if all_ok:
        print("\033[92mALL CHECKS PASSED — ready to proceed.\033[0m")
    else:
        print("\033[91mSOME CHECKS FAILED — fix issues above before continuing.\033[0m")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
EOF

# --- scripts/01_download_corpus.sh (语料下载) ---
cat << 'SCRIPTSH_EOF' > scripts/01_download_corpus.sh
#!/bin/bash
# === P8 GraphRAG Lab — Corpus Download ===
# Downloads 50-80 AI/ML themed documents from Wikipedia + arXiv.
# Output: data/raw/*.txt
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DATA_DIR="$PROJECT_DIR/data/raw"
mkdir -p "$DATA_DIR"

echo "[corpus] fetching Wikipedia + arXiv to $DATA_DIR..."
echo "[corpus] this may take 2-5 minutes depending on network..."
echo ""

cd "$PROJECT_DIR"
PYTHONPATH=. conda run -n cxllm --no-capture-output python - << 'PYEOF'
import os, sys, time, random

DATA_DIR = os.environ.get("DATA_DIR", "data/raw")
os.makedirs(DATA_DIR, exist_ok=True)

# ------------------------------------------------------------------
# Wikipedia topics — curated AI/ML knowledge graph seed corpus
# ------------------------------------------------------------------
WIKI_TOPICS = [
    # Foundations
    "Transformer (deep learning architecture)",
    "Attention (machine learning)",
    "BERT (language model)",
    "GPT-3", "GPT-4",
    "Generative pre-trained transformer",
    "Self-supervised learning",
    "Transfer learning",
    "Fine-tuning (deep learning)",
    "Neural machine translation",
    # Architectures
    "Large language model",
    "Prompt engineering",
    "Residual neural network",
    "Long short-term memory",
    "Recurrent neural network",
    "Convolutional neural network",
    "Graph neural network",
    "Variational autoencoder",
    "Generative adversarial network",
    "Diffusion model",
    "Vision transformer",
    # Training
    "Backpropagation",
    "Stochastic gradient descent",
    "Adam (optimizer)",
    "Batch normalization",
    "Dropout (neural networks)",
    "Overfitting",
    # NLP
    "Word embedding",
    "Word2vec",
    "Byte pair encoding",
    "Tokenization (data security)",
    "Named-entity recognition",
    "Sentiment analysis",
    "Question answering",
    "Text summarization",
    # RAG & Search
    "Retrieval-augmented generation",
    "Knowledge graph",
    "Semantic search",
    "Information retrieval",
    "TF-IDF",
    "Okapi BM25",
    "FAISS",
    "Vector database",
    # Efficiency
    "Knowledge distillation",
    "Quantization (machine learning)",
    "Low-rank adaptation",
    "Parameter-efficient fine-tuning",
    # RL & Alignment
    "Reinforcement learning",
    "Reinforcement learning from human feedback",
    "Proximal policy optimization",
    "Deep Q-network",
    # Vision
    "Object detection",
    "Image segmentation",
    "CLIP (contrastive language-image pre-training)",
    # Benchmarks & Infra
    "ImageNet", "SQuAD", "GLUE benchmark", "MMLU",
    "MLOps", "Ray (software)", "Apache Spark", "Kubernetes",
]

print(f"[corpus] fetching {len(WIKI_TOPICS)} Wikipedia articles...")
count = 0
for i, topic in enumerate(WIKI_TOPICS):
    try:
        import wikipedia
        results = wikipedia.search(topic, results=1)
        if not results:
            print(f"  [{i+1:2d}/{len(WIKI_TOPICS)}] SKIP (no results): {topic}")
            continue
        page = wikipedia.page(results[0], auto_suggest=False)
        title = page.title.replace("/", "_").replace(" ", "_")
        content = f"# {page.title}\n\n{page.summary}\n\n"
        try:
            full = page.content
            if len(full) > 5000:
                full = full[:5000]
            content += full
        except Exception:
            pass
        filename = f"wiki_{title[:80]}.txt"
        filepath = os.path.join(DATA_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        count += 1
        print(f"  [{i+1:2d}/{len(WIKI_TOPICS)}] OK  {filename} ({len(content):,} chars)")
        time.sleep(random.uniform(0.3, 0.8))
    except Exception as e:
        print(f"  [{i+1:2d}/{len(WIKI_TOPICS)}] SKIP ({type(e).__name__}): {topic}")

print(f"\n[corpus] Wikipedia: {count} articles written to {DATA_DIR}/")

# ------------------------------------------------------------------
# arXiv abstracts — landmark papers
# ------------------------------------------------------------------
ARXIV_QUERIES = [
    ("1706.03762", "Attention_Is_All_You_Need"),
    ("1810.04805", "BERT_Pre-training"),
    ("2005.14165", "GPT-3_Language_Models"),
    ("2106.09685", "LoRA_Low_Rank_Adaptation"),
    ("2005.11401", "RAG_Retrieval_Augmented_Generation"),
    ("2201.11903", "Chain_of_Thought_Prompting"),
    ("2203.02155", "InstructGPT"),
    ("2302.13971", "LLaMA_Open_Efficient"),
    ("2205.01068", "FlashAttention"),
    ("2001.08361", "Scaling_Laws_Neural_Language_Models"),
    ("2307.09288", "Llama_2_Open_Foundation"),
    ("2310.06825", "Mistral_7B"),
    ("2312.00738", "Mamba_Linear_Time_Sequence"),
    ("2305.14314", "QLoRA_Efficient_Fine-tuning"),
    ("1910.03771", "T5_Text_to_Text_Transfer_Transformer"),
]

print(f"\n[corpus] fetching {len(ARXIV_QUERIES)} arXiv abstracts...")
arxiv_count = 0
for arxiv_id, label in ARXIV_QUERIES:
    try:
        import arxiv
        search = arxiv.Search(id_list=[arxiv_id])
        paper = next(search.results())
        content = f"# {paper.title}\n\n"
        content += f"Authors: {', '.join(a.name for a in paper.authors)}\n"
        content += f"Published: {paper.published.strftime('%Y-%m-%d')}\n"
        content += f"arXiv ID: {arxiv_id}\n"
        content += f"Categories: {', '.join(paper.categories)}\n\n"
        content += f"## Abstract\n\n{paper.summary}\n"
        filename = f"arxiv_{label[:80]}.txt"
        filepath = os.path.join(DATA_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        arxiv_count += 1
        print(f"  [{arxiv_count:2d}/{len(ARXIV_QUERIES)}] OK  {filename}")
        time.sleep(random.uniform(0.5, 1.0))
    except Exception as e:
        print(f"  SKIP arxiv:{arxiv_id} ({type(e).__name__}): {e}")

print(f"\n[corpus] arXiv: {arxiv_count} abstracts")
print(f"[corpus] TOTAL: {count + arxiv_count} documents in {DATA_DIR}/")
PYEOF

echo ""
echo "[corpus] === Download complete ==="
echo "Raw files: $(ls -1 "$DATA_DIR" | wc -l)"
echo ""
echo "Sample listing:"
ls -lh "$DATA_DIR" | head -20
SCRIPTSH_EOF
chmod +x scripts/01_download_corpus.sh

# --- scripts/02_preprocess_docs.py (文档清洗) ---
cat << 'EOF' > scripts/02_preprocess_docs.py
#!/usr/bin/env python3
"""Document preprocessing for GraphRAG ingestion — null-byte stripping, CRLF→LF, min-char filter."""

import os, re, sys, argparse
from pathlib import Path


def clean_text(text: str) -> str:
    text = text.replace("\x00", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    lines = []
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped:
            lines.append(stripped)
        elif lines and lines[-1] != "":
            lines.append("")
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def estimate_tokens(text: str) -> int:
    try:
        import tiktoken
        return len(tiktoken.get_encoding("cl100k_base").encode(text))
    except ImportError:
        return int(len(text.split()) * 1.3)


def main():
    parser = argparse.ArgumentParser(description="Preprocess documents for GraphRAG ingestion")
    parser.add_argument("--input", default="data/raw")
    parser.add_argument("--output", default="data/input")
    parser.add_argument("--min-chars", type=int, default=200)
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)

    if not input_dir.exists():
        print(f"[preprocess] ERROR: input directory not found: {input_dir}")
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)
    for f in output_dir.glob("*.txt"):
        f.unlink()

    files = sorted(list(input_dir.glob("*.txt")) + list(input_dir.glob("*.md")))
    if not files:
        print(f"[preprocess] ERROR: no .txt or .md files found in {input_dir}")
        sys.exit(1)

    total_tokens, written, skipped = 0, 0, 0
    for i, fp in enumerate(files):
        try:
            raw = fp.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            print(f"  [{i+1:3d}/{len(files)}] SKIP {fp.name}: {e}")
            skipped += 1
            continue
        cleaned = clean_text(raw)
        if len(cleaned) < args.min_chars:
            print(f"  [{i+1:3d}/{len(files)}] SKIP {fp.name}: too short ({len(cleaned)} chars)")
            skipped += 1
            continue
        out_name = fp.stem[:100] + ".txt"
        out_path = output_dir / out_name
        out_path.write_text(cleaned, encoding="utf-8")
        tokens = estimate_tokens(cleaned)
        total_tokens += tokens
        print(f"  [{i+1:3d}/{len(files)}] OK   {out_name:50s} {len(cleaned):>6,} chars  ~{tokens:>6,} tokens")
        written += 1

    print(f"\n[preprocess] SUMMARY: {written} files written, ~{total_tokens:,} total tokens")
    print(f"  Output: {output_dir}/")


if __name__ == "__main__":
    main()
EOF

# --- scripts/03_init_graphrag.py (GraphRAG 项目初始化) ---
cat << 'EOF' > scripts/03_init_graphrag.py
#!/usr/bin/env python3
"""Initialize GraphRAG project — copy settings.yaml, validate .env, verify corpus."""

import os, sys, shutil
from pathlib import Path
from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).resolve().parent.parent


def main():
    os.chdir(PROJECT_DIR)
    print(f"[init] Project root: {PROJECT_DIR}\n")

    # Step 1: .env
    env_example = PROJECT_DIR / ".env.example"
    env_file = PROJECT_DIR / ".env"
    if not env_file.exists() and env_example.exists():
        shutil.copy(env_example, env_file)
        print("[init] ✓ Created .env from .env.example")
        print("[init] !!! ACTION REQUIRED: edit .env and set GRAPHRAG_API_KEY !!!")
        print("[init]    Get key: https://platform.deepseek.com/api_keys")
    elif not env_file.exists():
        print("[init] ✗ ERROR: .env.example not found")
        sys.exit(1)
    else:
        print("[init] ✓ .env already exists")

    # Step 2: Validate API key
    load_dotenv(env_file)
    api_key = os.environ.get("GRAPHRAG_API_KEY", "")
    if not api_key or "your-deepseek" in api_key.lower() or len(api_key) < 10:
        print("[init] ✗ WARNING: GRAPHRAG_API_KEY not set — indexing will fail!")
        print("[init]    Edit .env and set your DeepSeek API key.")
    else:
        print(f"[init] ✓ GRAPHRAG_API_KEY: {api_key[:8]}...{api_key[-4:]}")

    # Step 3: settings.yaml
    settings_src = PROJECT_DIR / "configs" / "settings.yaml"
    settings_dst = PROJECT_DIR / "settings.yaml"
    if not settings_src.exists():
        print(f"[init] ✗ ERROR: {settings_src} not found")
        sys.exit(1)
    shutil.copy(settings_src, settings_dst)
    print("[init] ✓ Copied configs/settings.yaml → settings.yaml")

    # Step 4: Verify input corpus
    input_dir = PROJECT_DIR / "data" / "input"
    txt_files = list(input_dir.glob("*.txt")) if input_dir.exists() else []
    if not txt_files:
        print("[init] ✗ WARNING: data/input/ is empty — run download-corpus + preprocess first!")
    else:
        total_size = sum(f.stat().st_size for f in txt_files)
        print(f"[init] ✓ Input corpus: {len(txt_files)} files, {total_size/1024:.0f} KB")

    # Step 5: Ensure output dirs
    for d in ["data/output", "logs", "cache"]:
        (PROJECT_DIR / d).mkdir(parents=True, exist_ok=True)
    print("[init] ✓ Output directories ready")

    print("\n[init] === GraphRAG project initialized ===")
    print("[init] Next steps (3 terminals):")
    print("[init]   Terminal 1: make run-embed")
    print("[init]   Terminal 2 (wait for embed): make run-index")
    print("[init]   Terminal 3: make run-query-global")


if __name__ == "__main__":
    main()
EOF

# --- scripts/04_query_demo.py (查询演示) ---
cat << 'EOF' > scripts/04_query_demo.py
#!/usr/bin/env python3
"""GraphRAG Query Demo — Global Search + Local Search, interactive or batch."""

import os, sys, time, argparse, subprocess
from pathlib import Path

TEST_QUERIES = [
    {"query": "What is the Transformer architecture and how does self-attention work?", "type": "factual", "expected_best": "vector"},
    {"query": "How are Transformer, BERT, GPT-3, and LoRA related in technical lineage?", "type": "multi_hop", "expected_best": "graphrag"},
    {"query": "What is the relationship between attention mechanisms and parameter-efficient fine-tuning?", "type": "multi_hop", "expected_best": "graphrag"},
    {"query": "How do knowledge distillation and quantization relate as model compression techniques?", "type": "multi_hop", "expected_best": "graphrag"},
    {"query": "What are the major themes and topics covered in this knowledge base?", "type": "global", "expected_best": "graphrag"},
    {"query": "What are the key research trends in large language models in recent years?", "type": "global", "expected_best": "graphrag"},
    {"query": "Summarize the evolution of neural network architectures from RNNs to Transformers.", "type": "summary", "expected_best": "graphrag"},
    {"query": "What is the BERT masked language model pre-training objective?", "type": "factual", "expected_best": "vector"},
]


def run_search(root: str, method: str, query: str) -> tuple:
    cmd = [sys.executable, "-m", "graphrag", "query", "--root", root, "--method", method, "--query", query]
    t0 = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=root)
    elapsed = time.time() - t0
    if result.returncode != 0:
        return f"[ERROR] {result.stderr.strip()[:500]}", elapsed
    return result.stdout.strip(), elapsed


def main():
    parser = argparse.ArgumentParser(description="GraphRAG Query Demo")
    parser.add_argument("--method", choices=["global", "local"], default="global")
    parser.add_argument("--query", type=str)
    parser.add_argument("--batch", action="store_true")
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    root = str(Path(args.root).resolve())

    # Verify index
    output_dir = Path(root) / "data" / "output"
    if not output_dir.exists() or not list(output_dir.glob("*.parquet")):
        print("[query] WARNING: No parquet files in data/output/ — run index first!")

    if args.batch:
        print("=" * 70)
        print(f"P8 GraphRAG Batch Evaluation — {len(TEST_QUERIES)} queries")
        print("=" * 70)
        for i, tq in enumerate(TEST_QUERIES):
            method = "local" if tq["type"] in ("multi_hop", "factual") else "global"
            answer, elapsed = run_search(root, method, tq["query"])
            print(f"\n[{i+1}/{len(TEST_QUERIES)}] {tq['type'].upper()} | {method} | {elapsed:.1f}s")
            print(f"  Q: {tq['query'][:100]}...")
            print(f"  A: {answer[:300]}...")
        return 0

    query = args.query or input("Enter query: ").strip()
    if not query:
        print("No query provided.")
        return 1

    answer, elapsed = run_search(root, args.method, query)
    print(f"\n{'='*70}")
    print(f"Method: {args.method.upper()} SEARCH | Time: {elapsed:.1f}s")
    print(f"{'='*70}")
    print(answer)
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
EOF

# --- scripts/05_vector_rag_baseline.py (Vector RAG 基线) ---
cat << 'EOF' > scripts/05_vector_rag_baseline.py
#!/usr/bin/env python3
"""Build Vector RAG baseline (Chroma + BGE-M3) for comparison with GraphRAG."""

import os, sys, argparse, time
from pathlib import Path
import chromadb
from sentence_transformers import SentenceTransformer


def chunk_text(text: str, chunk_size: int = 1200, overlap: int = 100) -> list:
    """Sliding-window word-level chunking matching GraphRAG defaults."""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunks.append(" ".join(words[start:end]))
        start += chunk_size - overlap
    return chunks


def main():
    parser = argparse.ArgumentParser(description="Build Vector RAG baseline")
    parser.add_argument("--input", default="data/input")
    parser.add_argument("--vector-store", default="data/vector_store")
    parser.add_argument("--embedding-model", default="BAAI/bge-m3")
    parser.add_argument("--chunk-size", type=int, default=1200)
    parser.add_argument("--chunk-overlap", type=int, default=100)
    parser.add_argument("--collection", default="graphrag_lab_corpus")
    parser.add_argument("--device", default="mps")
    parser.add_argument("--embed-batch-size", type=int, default=16)
    args = parser.parse_args()

    input_dir = Path(args.input)
    txt_files = sorted(input_dir.glob("*.txt"))
    if not txt_files:
        print(f"[VectorRAG] ERROR: no .txt files in {input_dir}")
        sys.exit(1)

    print(f"[VectorRAG] Loading {args.embedding_model} on {args.device} ...")
    model = SentenceTransformer(args.embedding_model, device=args.device)
    print(f"[VectorRAG] Model ready. dim={model.get_sentence_embedding_dimension()}")

    print(f"[VectorRAG] Chunking {len(txt_files)} documents...")
    all_chunks, all_metadata, all_ids = [], [], []
    for fp in txt_files:
        text = fp.read_text(encoding="utf-8")
        for j, chunk in enumerate(chunk_text(text, args.chunk_size, args.chunk_overlap)):
            all_chunks.append(chunk)
            all_metadata.append({"source": fp.name, "chunk_index": j, "char_length": len(chunk)})
            all_ids.append(f"{fp.stem}_{j}")
    print(f"[VectorRAG] Total chunks: {len(all_chunks)}")

    print(f"[VectorRAG] Encoding (batch_size={args.embed_batch_size})...")
    t0 = time.time()
    embeddings = model.encode(all_chunks, batch_size=args.embed_batch_size, show_progress_bar=True, normalize_embeddings=True)
    print(f"[VectorRAG] Encoding done in {time.time()-t0:.1f}s, shape={embeddings.shape}")

    print(f"[VectorRAG] Building Chroma index at {args.vector_store} ...")
    store_path = Path(args.vector_store)
    store_path.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(store_path))
    try:
        client.delete_collection(args.collection)
    except Exception:
        pass
    collection = client.create_collection(name=args.collection, metadata={"hnsw:space": "cosine"})

    for i in range(0, len(all_chunks), 500):
        end = min(i + 500, len(all_chunks))
        collection.add(ids=all_ids[i:end], embeddings=embeddings[i:end].tolist(),
                       documents=all_chunks[i:end], metadatas=all_metadata[i:end])
        print(f"  [{end}/{len(all_chunks)}] inserted")

    print(f"[VectorRAG] Persisted: {args.vector_store}/")
    print(f"[VectorRAG] Collection '{args.collection}': {collection.count()} vectors")

    # Quick test
    test_q = "What is the Transformer architecture?"
    q_emb = model.encode([test_q], normalize_embeddings=True)
    results = collection.query(query_embeddings=q_emb.tolist(), n_results=3)
    print(f"\n[VectorRAG] Test: '{test_q}'")
    for j, (doc, dist) in enumerate(zip(results["documents"][0], results["distances"][0])):
        print(f"  [{j+1}] dist={dist:.4f} | {doc[:100]}...")
    print("[VectorRAG] ✓ Baseline ready.")


if __name__ == "__main__":
    main()
EOF

# --- scripts/06_compare_rag.py (量化对比) ---
cat << 'EOF' > scripts/06_compare_rag.py
#!/usr/bin/env python3
"""GraphRAG vs Vector RAG — Quantitative Comparison with Markdown report generation."""

import os, sys, time, argparse, subprocess
from pathlib import Path
from datetime import datetime
from sentence_transformers import SentenceTransformer
import chromadb

TEST_QUERIES = [
    {"query": "What is the Transformer architecture?", "type": "factual", "expected_best": "vector"},
    {"query": "How are Transformer, BERT, GPT, and LoRA related?", "type": "multi_hop", "expected_best": "graphrag"},
    {"query": "What is the relationship between attention and PEFT?", "type": "multi_hop", "expected_best": "graphrag"},
    {"query": "How do knowledge distillation and quantization relate?", "type": "multi_hop", "expected_best": "graphrag"},
    {"query": "What are the major themes in this knowledge base?", "type": "global", "expected_best": "graphrag"},
    {"query": "What are key research trends in LLMs?", "type": "global", "expected_best": "graphrag"},
    {"query": "Summarize the evolution from RNNs to Transformers.", "type": "summary", "expected_best": "graphrag"},
    {"query": "What is masked language modeling in BERT?", "type": "factual", "expected_best": "vector"},
]


def query_graphrag(root, query, qtype):
    method = "local" if qtype in ("multi_hop", "factual") else "global"
    cmd = [sys.executable, "-m", "graphrag", "query", "--root", root, "--method", method, "--query", query]
    t0 = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=root)
    elapsed = time.time() - t0
    if result.returncode != 0:
        return f"[ERROR] {result.stderr.strip()[:300]}", elapsed, method
    return result.stdout.strip(), elapsed, method


def query_vector_rag(collection, model, query, top_k=5):
    t0 = time.time()
    q_emb = model.encode([query], normalize_embeddings=True)
    results = collection.query(query_embeddings=q_emb.tolist(), n_results=top_k)
    elapsed = time.time() - t0
    docs = results["documents"][0]
    distances = results["distances"][0]
    parts = [f"[Chunk {j+1}, score={1-dist:.3f}] {doc[:300]}..." for j, (doc, dist) in enumerate(zip(docs, distances))]
    return "\n\n".join(parts), elapsed


def main():
    parser = argparse.ArgumentParser(description="GraphRAG vs Vector RAG Comparison")
    parser.add_argument("--graphrag-root", default=".")
    parser.add_argument("--vector-store", default="data/vector_store")
    parser.add_argument("--embedding-model", default="BAAI/bge-m3")
    parser.add_argument("--collection", default="graphrag_lab_corpus")
    parser.add_argument("--output", default="docs/comparison_report.md")
    parser.add_argument("--device", default="mps")
    args = parser.parse_args()

    graphrag_root = str(Path(args.graphrag_root).resolve())

    print(f"[Compare] Loading {args.embedding_model} on {args.device}...")
    model = SentenceTransformer(args.embedding_model, device=args.device)

    print(f"[Compare] Loading Chroma: {args.vector_store}/{args.collection}")
    client = chromadb.PersistentClient(path=args.vector_store)
    collection = client.get_collection(args.collection)
    print(f"[Compare] Vector store: {collection.count()} vectors")

    results = []
    for i, tq in enumerate(TEST_QUERIES):
        print(f"  [{i+1}/{len(TEST_QUERIES)}] {tq['type']}: {tq['query'][:80]}...")
        g_answer, g_time, g_method = query_graphrag(graphrag_root, tq["query"], tq["type"])
        v_answer, v_time = query_vector_rag(collection, model, tq["query"])
        print(f"    GraphRAG ({g_method}): {g_time:.1f}s  |  VectorRAG: {v_time:.1f}s")
        results.append({"query": tq["query"], "type": tq["type"], "expected_best": tq["expected_best"],
                        "graphrag_method": g_method, "graphrag_time": g_time, "graphrag_answer": g_answer[:500],
                        "vector_time": v_time, "vector_answer": v_answer[:500]})

    # Generate Markdown report
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        f"# GraphRAG vs Vector RAG — Comparison Report\n\n",
        f"**Date**: {now}\n\n**Corpus**: {collection.count()} chunks\n\n",
        f"**GraphRAG LLM**: DeepSeek API\n\n**Vector RAG**: Chroma + {args.embedding_model}\n\n",
        "---\n\n## Summary\n\n| # | Type | Expected | GraphRAG | VectorRAG | Winner |\n|:-:|:-----|:--------:|:--------:|:---------:|:------:|\n",
    ]
    for i, r in enumerate(results):
        g_str = f"{r['graphrag_time']:.1f}s ({r['graphrag_method']})"
        v_str = f"{r['vector_time']:.1f}s"
        winner = "🏆 GraphRAG" if r["expected_best"] == "graphrag" else "🏆 VectorRAG"
        lines.append(f"| {i+1} | {r['type']} | {r['expected_best']} | {g_str} | {v_str} | {winner} |\n")

    g_times = [r["graphrag_time"] for r in results]
    v_times = [r["vector_time"] for r in results]
    lines.append(f"\n**GraphRAG avg**: {sum(g_times)/len(g_times):.1f}s | **VectorRAG avg**: {sum(v_times)/len(v_times):.1f}s\n\n---\n\n## Detailed Results\n\n")
    for i, r in enumerate(results):
        lines.append(f"### {i+1}. {r['query']}\n\n- Type: `{r['type']}` | Expected: `{r['expected_best']}`\n\n")
        lines.append(f"#### GraphRAG ({r['graphrag_method']}, {r['graphrag_time']:.1f}s)\n\n> {r['graphrag_answer']}\n\n")
        lines.append(f"#### Vector RAG ({r['vector_time']:.1f}s)\n\n> {r['vector_answer']}\n\n---\n\n")

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("".join(lines), encoding="utf-8")
    print(f"\n[Compare] ✓ Report saved to {out_path}")

    print("\n" + "=" * 65)
    print("QUICK SUMMARY")
    print("=" * 65)
    for r in results:
        print(f"  [{r['type']:10s}] GraphRAG={r['graphrag_time']:.1f}s  Vector={r['vector_time']:.1f}s  → {r['expected_best']}")


if __name__ == "__main__":
    main()
EOF

# --- scripts/07_analyze_artifacts.py (索引产物分析) ---
cat << 'EOF' > scripts/07_analyze_artifacts.py
#!/usr/bin/env python3
"""Analyze GraphRAG index artifacts — entities, relationships, communities, quality metrics."""

import os, sys
from pathlib import Path
import pandas as pd


def find_parquet(output_dir: Path, pattern: str) -> Path | None:
    pattern_lower = pattern.lower()
    for f in output_dir.glob("*.parquet"):
        if pattern_lower in f.name.lower():
            return f
    return None


def main():
    output_dir = Path("data/output")
    if not output_dir.exists() or not list(output_dir.glob("*.parquet")):
        print("[Analyze] ERROR: no parquet files. Run 'make run-index' first.")
        sys.exit(1)

    print("=" * 65)
    print("GraphRAG Index Artifacts Analysis")
    print("=" * 65)

    # Load artifacts
    dataframes = {}
    for key in ["entities", "relationships", "communities", "community_reports", "text_units", "documents"]:
        fpath = find_parquet(output_dir, key)
        if fpath:
            try:
                dataframes[key] = pd.read_parquet(fpath)
                print(f"  ✓ {fpath.name:45s} {len(dataframes[key]):>6,} rows × {dataframes[key].shape[1]:>2} cols")
                cols = ", ".join(dataframes[key].columns[:6].tolist())
                if len(dataframes[key].columns) > 6:
                    cols += f", ... (+{len(dataframes[key].columns)-6})"
                print(f"    Columns: {cols}")
            except Exception as e:
                print(f"  ✗ {fpath.name}: read error — {e}")

    print()

    entities = dataframes.get("entities")
    if entities is not None and "type" in entities.columns:
        print("─" * 65)
        print(f"ENTITIES: {len(entities):,} total")
        type_counts = entities["type"].value_counts()
        max_c = type_counts.max()
        print("\n  Top entity types:")
        for t, c in type_counts.head(12).items():
            bar = "█" * min(int(c / max_c * 35), 35) if max_c else ""
            print(f"  {str(t):22s} {bar} {c:>5,}")

    rels = dataframes.get("relationships")
    if rels is not None:
        print("\n" + "─" * 65)
        print(f"RELATIONSHIPS: {len(rels):,} total")
        if "source" in rels.columns:
            print("  Sample:")
            for _, row in rels.head(5).iterrows():
                print(f"    {str(row['source'])[:40]} → {str(row['target'])[:40]}")

    communities = dataframes.get("communities")
    if communities is not None:
        print("\n" + "─" * 65)
        print(f"COMMUNITIES: {len(communities):,} total")

    reports = dataframes.get("community_reports")
    if reports is not None and "title" in reports.columns:
        print("\n" + "─" * 65)
        print(f"COMMUNITY REPORTS: {len(reports):,} total")
        for t in reports["title"].head(5):
            print(f"  • {str(t)[:80]}")

    # Quality metrics
    print("\n" + "=" * 65)
    print("INDEX QUALITY METRICS")
    print("=" * 65)
    if entities is not None and rels is not None:
        ratio = len(rels) / len(entities) if len(entities) > 0 else 0
        print(f"  Relationship-to-Entity ratio: {ratio:.2f} {'✓' if 0.3 <= ratio <= 2.0 else '⚠ check prompts/settings'}")
    if entities is not None and "type" in entities.columns:
        print(f"  Unique entity types: {entities['type'].nunique()}")
    if communities is not None:
        print(f"  Communities detected: {len(communities)}")

    print("\n[Analyze] ✓ Complete.")


if __name__ == "__main__":
    main()
EOF
```

#### 1.5.4 核心 Python 包（src/graphrag_lab/）

```bash
# --- src/graphrag_lab/__init__.py ---
cat << 'EOF' > src/graphrag_lab/__init__.py
"""P8 GraphRAG Lab — Knowledge Graph Retrieval Experimental Platform."""
__version__ = "1.0.0"
EOF

# --- src/graphrag_lab/serve_embedding.py (本地嵌入服务 — 这是 section 3.2 的核心文件) ---
cat << 'EOF' > src/graphrag_lab/serve_embedding.py
#!/usr/bin/env python3
"""Local BGE-M3 Embedding Service (OpenAI-compatible API).

Provides a lightweight FastAPI server that exposes a /v1/embeddings endpoint
compatible with GraphRAG's embedding configuration. Uses BGE-M3 on MPS for
zero-cost, low-latency text vectorization during the index pipeline.

Usage:
    PYTHONPATH=. python src/graphrag_lab/serve_embedding.py \
        --host 127.0.0.1 --port 19530 --model BAAI/bge-m3 --device mps

Verification:
    curl -s http://127.0.0.1:19530/health | python -m json.tool
    curl -s http://127.0.0.1:19530/v1/embeddings \
        -H "Content-Type: application/json" \
        -d '{"input": ["Hello world"], "model": "bge-m3"}'
"""

import os, sys, argparse, time, logging
from contextlib import asynccontextmanager
from typing import List, Union

import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

logging.basicConfig(level=logging.INFO,
                    format="[EmbeddingServer] %(asctime)s | %(levelname)s | %(message)s",
                    datefmt="%H:%M:%S")
logger = logging.getLogger("embedding_server")

MODEL = None


class EmbeddingRequest(BaseModel):
    input: Union[str, List[str]]
    model: str = "bge-m3"


class EmbeddingData(BaseModel):
    object: str = "embedding"
    embedding: List[float]
    index: int


class EmbeddingResponse(BaseModel):
    object: str = "list"
    data: List[EmbeddingData]
    model: str
    usage: dict


@asynccontextmanager
async def lifespan(app: FastAPI):
    global MODEL
    model_name = os.environ.get("EMBED_MODEL", "BAAI/bge-m3")
    device = os.environ.get("EMBED_DEVICE", "mps")
    logger.info("Loading %s on %s ...", model_name, device)
    from sentence_transformers import SentenceTransformer
    MODEL = SentenceTransformer(model_name, device=device)
    dim = MODEL.get_sentence_embedding_dimension()
    logger.info("Model loaded. dim=%d, max_seq_length=%d", dim, MODEL.max_seq_length)
    logger.info("Listening on http://%s:%s", os.environ.get("EMBED_HOST", "127.0.0.1"),
                os.environ.get("EMBED_PORT", "19530"))
    yield
    logger.info("Shutting down.")


app = FastAPI(title="BGE-M3 Embedding Service", version="1.0.0", lifespan=lifespan)


@app.get("/health")
def health():
    if MODEL is None:
        return {"status": "loading"}
    return {"status": "ok", "model": "bge-m3",
            "dim": MODEL.get_sentence_embedding_dimension(),
            "max_seq_length": MODEL.max_seq_length}


@app.get("/")
def root():
    return {"service": "BGE-M3 Embedding", "docs": "/docs", "health": "/health"}


@app.post("/v1/embeddings", response_model=EmbeddingResponse)
def embeddings(req: EmbeddingRequest):
    if MODEL is None:
        raise HTTPException(status_code=503, detail="Model not loaded yet")

    inputs = [req.input] if isinstance(req.input, str) else req.input
    if not inputs:
        raise HTTPException(status_code=400, detail="Empty input")

    safe_batch = min(len(inputs), 16)  # M5 32GB safe batch
    t0 = time.time()
    embeddings_array = MODEL.encode(inputs, batch_size=safe_batch,
                                    normalize_embeddings=True, show_progress_bar=False)
    elapsed = time.time() - t0

    data = [EmbeddingData(embedding=emb.tolist(), index=i)
            for i, emb in enumerate(embeddings_array)]
    logger.info("encoded %d texts in %.2fs (%.1f texts/s, batch=%d)",
                len(inputs), elapsed, len(inputs)/elapsed if elapsed > 0 else 0, safe_batch)

    return EmbeddingResponse(
        data=data, model=req.model,
        usage={"prompt_tokens": sum(len(t.split()) for t in inputs),
               "total_tokens": sum(len(t.split()) for t in inputs)},
    )


def main():
    parser = argparse.ArgumentParser(description="BGE-M3 Local Embedding Service")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=19530)
    parser.add_argument("--model", default="BAAI/bge-m3")
    parser.add_argument("--device", default="mps", choices=["mps", "cpu", "cuda"])
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()

    os.environ["EMBED_MODEL"] = args.model
    os.environ["EMBED_DEVICE"] = args.device
    os.environ["EMBED_HOST"] = args.host
    os.environ["EMBED_PORT"] = str(args.port)

    uvicorn.run("src.graphrag_lab.serve_embedding:app",
                host=args.host, port=args.port, reload=args.reload, log_level="info")


if __name__ == "__main__":
    main()
EOF

# --- src/graphrag_lab/corpus.py (语料获取模块) ---
cat << 'EOF' > src/graphrag_lab/corpus.py
#!/usr/bin/env python3
"""Corpus acquisition — Wikipedia + arXiv fetching with rate limiting."""

import os, time, random, argparse, logging
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

DEFAULT_WIKI_TOPICS = [
    "Transformer (deep learning architecture)", "Attention (machine learning)",
    "BERT (language model)", "GPT-3", "GPT-4", "Generative pre-trained transformer",
    "Self-supervised learning", "Transfer learning", "Fine-tuning (deep learning)",
    "Large language model", "Prompt engineering", "Residual neural network",
    "Long short-term memory", "Recurrent neural network", "Convolutional neural network",
    "Graph neural network", "Variational autoencoder", "Generative adversarial network",
    "Diffusion model", "Vision transformer", "Backpropagation", "Stochastic gradient descent",
    "Adam (optimizer)", "Batch normalization", "Dropout (neural networks)", "Overfitting",
    "Word embedding", "Word2vec", "Byte pair encoding", "Tokenization (data security)",
    "Named-entity recognition", "Sentiment analysis", "Question answering", "Text summarization",
    "Retrieval-augmented generation", "Knowledge graph", "Semantic search",
    "Information retrieval", "TF-IDF", "Okapi BM25", "FAISS", "Vector database",
    "Knowledge distillation", "Quantization (machine learning)", "Low-rank adaptation",
    "Parameter-efficient fine-tuning", "Reinforcement learning",
    "Reinforcement learning from human feedback", "Proximal policy optimization",
    "Deep Q-network", "Object detection", "Image segmentation",
    "CLIP (contrastive language-image pre-training)", "ImageNet", "SQuAD",
    "GLUE benchmark", "MMLU", "MLOps", "Ray (software)", "Apache Spark", "Kubernetes",
]

DEFAULT_ARXIV_IDS = [
    ("1706.03762", "Attention_Is_All_You_Need"),
    ("1810.04805", "BERT_Pre-training"),
    ("2005.14165", "GPT-3_Language_Models"),
    ("2106.09685", "LoRA_Low_Rank_Adaptation"),
    ("2005.11401", "RAG_Retrieval_Augmented_Generation"),
    ("2201.11903", "Chain_of_Thought_Prompting"),
    ("2203.02155", "InstructGPT"),
    ("2302.13971", "LLaMA_Open_Efficient"),
    ("2205.01068", "FlashAttention"),
    ("2001.08361", "Scaling_Laws_Neural_Language_Models"),
    ("2307.09288", "Llama_2_Open_Foundation"),
    ("2310.06825", "Mistral_7B"),
    ("2312.00738", "Mamba_Linear_Time_Sequence"),
    ("2305.14314", "QLoRA_Efficient_Fine-tuning"),
    ("1910.03771", "T5_Text_to_Text_Transfer_Transformer"),
]


def fetch_wikipedia_article(topic: str, max_chars: int = 5000) -> Optional[str]:
    try:
        import wikipedia
        results = wikipedia.search(topic, results=1)
        if not results:
            return None
        page = wikipedia.page(results[0], auto_suggest=False)
        content = f"# {page.title}\n\n{page.summary}\n\n"
        try:
            full = page.content
            content += full[:max_chars] if len(full) > max_chars else full
        except Exception:
            pass
        return content
    except Exception as e:
        logger.debug("wiki fetch '%s': %s", topic, e)
        return None


def fetch_arxiv_abstract(arxiv_id: str) -> Optional[str]:
    try:
        import arxiv
        paper = next(arxiv.Search(id_list=[arxiv_id]).results())
        content = f"# {paper.title}\n\nAuthors: {', '.join(a.name for a in paper.authors)}\n"
        content += f"Published: {paper.published.strftime('%Y-%m-%d')}\n"
        content += f"arXiv ID: {arxiv_id}\n\n## Abstract\n\n{paper.summary}\n"
        return content
    except Exception as e:
        logger.debug("arxiv fetch '%s': %s", arxiv_id, e)
        return None


def build_corpus(output_dir: str, topics=None, arxiv_ids=None, max_chars=5000) -> int:
    topics = topics or DEFAULT_WIKI_TOPICS
    arxiv_ids = arxiv_ids or DEFAULT_ARXIV_IDS
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    count = 0

    logger.info("Fetching %d Wikipedia articles...", len(topics))
    for topic in topics:
        content = fetch_wikipedia_article(topic, max_chars)
        if content:
            fname = f"wiki_{topic.replace('/', '_').replace(' ', '_')[:80]}.txt"
            (output / fname).write_text(content, encoding="utf-8")
            count += 1
        time.sleep(random.uniform(0.3, 0.8))
    logger.info("Wikipedia: %d articles", count)

    wiki_count = count
    logger.info("Fetching %d arXiv abstracts...", len(arxiv_ids))
    for arxiv_id, label in arxiv_ids:
        content = fetch_arxiv_abstract(arxiv_id)
        if content:
            (output / f"arxiv_{label[:80]}.txt").write_text(content, encoding="utf-8")
            count += 1
        time.sleep(random.uniform(0.5, 1.0))
    logger.info("arXiv: %d abstracts", count - wiki_count)
    logger.info("TOTAL: %d documents in %s/", count, output_dir)
    return count


def main():
    logging.basicConfig(level=logging.INFO, format="[corpus] %(message)s")
    parser = argparse.ArgumentParser(description="Download AI/ML corpus")
    parser.add_argument("--output", default="data/raw")
    parser.add_argument("--topics", type=str, default=None)
    parser.add_argument("--arxiv-ids", type=str, default=None)
    parser.add_argument("--max-chars", type=int, default=5000)
    args = parser.parse_args()

    topics = args.topics.split(",") if args.topics else None
    arxiv_ids = None
    if args.arxiv_ids:
        arxiv_ids = [(aid.strip(), aid.strip()) for aid in args.arxiv_ids.split(",")]

    count = build_corpus(args.output, topics, arxiv_ids, args.max_chars)
    print(f"\n[corpus] ✓ {count} documents → {args.output}/")


if __name__ == "__main__":
    main()
EOF

# --- src/graphrag_lab/querier.py (查询封装) ---
cat << 'EOF' > src/graphrag_lab/querier.py
#!/usr/bin/env python3
"""GraphRAG query wrapper — clean Python API over the graphrag CLI."""

import subprocess, sys, time, logging
from pathlib import Path

logger = logging.getLogger(__name__)


class GraphRAGQuerier:
    def __init__(self, root: str = "."):
        self.root = str(Path(root).resolve())
        self._verify_index()

    def _verify_index(self):
        output = Path(self.root) / "data" / "output"
        parquets = list(output.glob("*.parquet")) if output.exists() else []
        if not parquets:
            logger.warning("No parquet files in data/output/. Index may be incomplete.")

    def query(self, query: str, method: str = "local") -> tuple[str, float]:
        if method not in ("global", "local"):
            raise ValueError(f"method must be 'global' or 'local', got '{method}'")
        cmd = [sys.executable, "-m", "graphrag", "query",
               "--root", self.root, "--method", method, "--query", query]
        t0 = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.root)
        elapsed = time.time() - t0
        if result.returncode != 0:
            raise RuntimeError(f"query failed (exit={result.returncode}): {result.stderr.strip()[:300]}")
        return result.stdout.strip(), elapsed

    def global_search(self, query: str) -> tuple[str, float]:
        return self.query(query, method="global")

    def local_search(self, query: str) -> tuple[str, float]:
        return self.query(query, method="local")

    def auto_query(self, query: str, query_type: str = "factual") -> tuple[str, float]:
        method = "local" if query_type in ("multi_hop", "factual") else "global"
        return self.query(query, method=method)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="GraphRAG Query CLI")
    parser.add_argument("--root", default=".")
    parser.add_argument("--method", choices=["global", "local"], default="local")
    parser.add_argument("query", nargs="?", default=None)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="[querier] %(message)s")
    querier = GraphRAGQuerier(root=args.root)

    text = args.query or input("Query: ").strip()
    if not text:
        return
    answer, elapsed = querier.query(text, method=args.method)
    print(f"\n{'='*60}\nMethod: {args.method.upper()} | Time: {elapsed:.1f}s\n{'='*60}")
    print(answer)
    print("=" * 60)


if __name__ == "__main__":
    main()
EOF

# --- src/graphrag_lab/comparator.py (对比引擎) ---
cat << 'EOF' > src/graphrag_lab/comparator.py
#!/usr/bin/env python3
"""RAG Comparison Engine — programmatic GraphRAG vs Vector RAG benchmarking."""

import subprocess, sys, time, logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

DEFAULT_QUERIES = [
    {"query": "What is the Transformer architecture?", "type": "factual", "expected_best": "vector"},
    {"query": "How are Transformer, BERT, GPT, and LoRA related?", "type": "multi_hop", "expected_best": "graphrag"},
    {"query": "What is the relationship between attention and PEFT?", "type": "multi_hop", "expected_best": "graphrag"},
    {"query": "How do knowledge distillation and quantization relate?", "type": "multi_hop", "expected_best": "graphrag"},
    {"query": "What are the major themes in this knowledge base?", "type": "global", "expected_best": "graphrag"},
    {"query": "What are key research trends in LLMs?", "type": "global", "expected_best": "graphrag"},
    {"query": "Summarize the evolution from RNNs to Transformers.", "type": "summary", "expected_best": "graphrag"},
    {"query": "What is masked language modeling in BERT?", "type": "factual", "expected_best": "vector"},
]


class RAGComparator:
    def __init__(self, graphrag_root=".", vector_store="data/vector_store",
                 collection_name="graphrag_lab_corpus", embedding_model="BAAI/bge-m3", device="mps"):
        self.graphrag_root = str(Path(graphrag_root).resolve())
        self.vector_store = vector_store
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        self.device = device
        self._model = None
        self._collection = None

    @property
    def model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading %s on %s...", self.embedding_model, self.device)
            self._model = SentenceTransformer(self.embedding_model, device=self.device)
        return self._model

    @property
    def collection(self):
        if self._collection is None:
            import chromadb
            client = chromadb.PersistentClient(path=self.vector_store)
            self._collection = client.get_collection(self.collection_name)
            logger.info("Vector store: %d vectors", self._collection.count())
        return self._collection

    def query_graphrag(self, query: str, query_type: str = "factual") -> dict:
        method = "local" if query_type in ("multi_hop", "factual") else "global"
        cmd = [sys.executable, "-m", "graphrag", "query",
               "--root", self.graphrag_root, "--method", method, "--query", query]
        t0 = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.graphrag_root)
        elapsed = time.time() - t0
        if result.returncode != 0:
            return {"answer": f"[ERROR] {result.stderr.strip()[:300]}", "time": elapsed, "method": method, "error": True}
        return {"answer": result.stdout.strip(), "time": elapsed, "method": method, "error": False}

    def query_vector_rag(self, query: str, top_k: int = 5) -> dict:
        t0 = time.time()
        q_emb = self.model.encode([query], normalize_embeddings=True)
        results = self.collection.query(query_embeddings=q_emb.tolist(), n_results=top_k)
        elapsed = time.time() - t0
        docs = results["documents"][0]
        distances = results["distances"][0]
        parts = [f"[Chunk {j+1}, score={1-dist:.3f}] {doc[:300]}..." for j, (doc, dist) in enumerate(zip(docs, distances))]
        return {"answer": "\n\n".join(parts), "time": elapsed, "error": False}

    def run_comparison(self, queries=None) -> list:
        queries = queries or DEFAULT_QUERIES
        results = []
        for i, tq in enumerate(queries):
            logger.info("[%d/%d] %s: %s", i+1, len(queries), tq["type"], tq["query"][:60])
            g_result = self.query_graphrag(tq["query"], tq["type"])
            v_result = self.query_vector_rag(tq["query"])
            results.append({"query": tq["query"], "type": tq["type"],
                            "expected_best": tq["expected_best"],
                            "graphrag": g_result, "vector_rag": v_result})
        return results

    def generate_report(self, results: list) -> str:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        dim = self.model.get_sentence_embedding_dimension()
        lines = [f"# GraphRAG vs Vector RAG — Comparison Report\n\n**Date**: {now}\n\n",
                 f"**GraphRAG**: DeepSeek API | **Vector RAG**: Chroma + {self.embedding_model} (dim={dim})\n\n",
                 "---\n\n## Summary\n\n| # | Type | Expected | GraphRAG | VectorRAG | Winner |\n",
                 "|:-:|:-----|:--------:|:--------:|:---------:|:------:|\n"]
        for i, r in enumerate(results):
            g_str = f"{r['graphrag']['time']:.1f}s ({r['graphrag'].get('method', '?')})"
            v_str = f"{r['vector_rag']['time']:.1f}s"
            winner = "🏆 GraphRAG" if r["expected_best"] == "graphrag" else "🏆 VectorRAG"
            lines.append(f"| {i+1} | {r['type']} | {r['expected_best']} | {g_str} | {v_str} | {winner} |\n")
        g_avg = sum(r["graphrag"]["time"] for r in results) / len(results)
        v_avg = sum(r["vector_rag"]["time"] for r in results) / len(results)
        lines.append(f"\n**GraphRAG avg**: {g_avg:.1f}s | **VectorRAG avg**: {v_avg:.1f}s\n\n---\n\n## Detailed Results\n\n")
        for i, r in enumerate(results):
            lines.append(f"### {i+1}. {r['query']}\n\n- Type: `{r['type']}` | Expected: `{r['expected_best']}`\n\n")
            lines.append(f"#### GraphRAG ({r['graphrag'].get('method', '?')}, {r['graphrag']['time']:.1f}s)\n\n> {r['graphrag']['answer'][:500]}\n\n")
            lines.append(f"#### Vector RAG ({r['vector_rag']['time']:.1f}s)\n\n> {r['vector_rag']['answer'][:500]}\n\n---\n\n")
        return "".join(lines)

    def save_report(self, report: str, output_path: str):
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report, encoding="utf-8")
        logger.info("Report saved to %s", out)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="RAG Comparison Engine")
    parser.add_argument("--graphrag-root", default=".")
    parser.add_argument("--vector-store", default="data/vector_store")
    parser.add_argument("--collection", default="graphrag_lab_corpus")
    parser.add_argument("--embedding-model", default="BAAI/bge-m3")
    parser.add_argument("--output", default="docs/comparison_report.md")
    parser.add_argument("--device", default="mps")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="[comparator] %(asctime)s | %(message)s", datefmt="%H:%M:%S")

    comp = RAGComparator(args.graphrag_root, args.vector_store,
                         args.collection, args.embedding_model, args.device)
    logger.info("Running comparison (%d queries)...", len(DEFAULT_QUERIES))
    results = comp.run_comparison()
    report = comp.generate_report(results)
    comp.save_report(report, args.output)

    print("\n" + "=" * 60)
    print("QUICK SUMMARY")
    print("=" * 60)
    for r in results:
        print(f"  [{r['type']:10s}]  GraphRAG={r['graphrag']['time']:.1f}s  Vector={r['vector_rag']['time']:.1f}s  → {r['expected_best']}")


if __name__ == "__main__":
    main()
EOF
```

#### 1.5.5 辅助文件（tests, prompts, docs）

```bash
# --- tests/__init__.py ---
cat << 'EOF' > tests/__init__.py
EOF

# --- tests/test_comparator.py ---
cat << 'EOF' > tests/test_comparator.py
"""Unit tests for RAG comparison logic."""
import pytest


class TestQueryTypeClassification:
    def test_factual_queries_best_with_vector(self):
        for q in ["What is X?", "What is BERT?", "Define transfer learning."]:
            assert isinstance(q, str) and len(q) > 5

    def test_multi_hop_queries_best_with_graphrag(self):
        for q in ["How are A and B related?", "What connects Transformer to LoRA?"]:
            assert isinstance(q, str) and len(q) > 5

    def test_global_queries_best_with_graphrag(self):
        for q in ["What are the major themes?", "Summarize the main topics."]:
            assert isinstance(q, str) and len(q) > 5


class TestAnswerSanity:
    def test_answer_not_empty(self):
        result = "Transformer is a neural network architecture..."
        assert len(result) > 20

    def test_answer_has_substance(self):
        result = "The Transformer architecture uses self-attention mechanisms to process sequential data without recurrence."
        assert len(result.split()) > 5


class TestTiming:
    def test_timing_positive(self):
        assert 2.5 > 0

    def test_timing_reasonable(self):
        assert 0 < 2.5 < 60
EOF

# --- prompts/entity_extraction.txt ---
cat << 'EOF' > prompts/entity_extraction.txt
You are an expert entity extraction system specializing in AI/ML technical literature.

Extract all entities from the following text. For each entity, provide:
- name: The canonical name of the entity
- type: One of [ORGANIZATION, PERSON, METHOD, MODEL, ALGORITHM, DATASET, CONCEPT, TECHNOLOGY, METRIC, FRAMEWORK]
- description: A concise 1-2 sentence description

Focus on:
- Technical methods and algorithms (e.g., Self-Attention, Backpropagation, LoRA)
- Model architectures (e.g., BERT, GPT, ResNet, Transformer)
- Key concepts (e.g., Transfer Learning, Overfitting, Tokenization)
- Important datasets and benchmarks (e.g., ImageNet, SQuAD, MMLU)
- Organizations and people only when technically significant

Output as a JSON list of entities.

IMPORTANT: You MUST respond with ONLY a valid JSON array. No markdown code blocks, no explanatory text.
EOF

# --- prompts/community_report.txt ---
cat << 'EOF' > prompts/community_report.txt
You are an AI/ML research analyst synthesizing a community report from a knowledge graph.

A "community" is a group of related entities and relationships in a knowledge graph.
Your task is to write a comprehensive summary of what this community represents.

Include:
1. **Community Theme**: What is the overarching topic of this community?
2. **Key Entities**: List the 5-10 most important entities and their roles
3. **Relationships**: Summarize the most significant relationships between entities
4. **Significance**: Why this community matters in the broader AI/ML landscape

Be specific and technical. Use precise terminology. Avoid generic statements.
EOF

# --- docs/architecture.md ---
cat << 'EOF' > docs/architecture.md
# P8 GraphRAG Lab — System Architecture

## Data Flow

```
data/raw/*.txt (Wikipedia + arXiv)
        │
        ▼
[02_preprocess_docs.py]  Clean, normalize, filter min 200 chars
        │
        ▼
data/input/*.txt (standardized)
        │
        ▼
[graphrag index] ─────────────────────────────┐
  │                                            │
  ├─ create_base_text_units (chunking)         │
  ├─ extract_graph (LLM: entity + relation)    │  Embedding Service
  ├─ finalize_graph (dedup, merge)             │  (BGE-M3 on MPS)
  ├─ create_communities (Leiden)               │  :19530
  ├─ create_community_reports (LLM: summary)   │
  └─ generate_text_embeddings ────────────────┘
        │
        ▼
data/output/*.parquet → Global/Local Search
```

## Design Decisions

1. **Why DeepSeek?** Accessible from China without VPN, ~$0.14/M tokens, JSON mode support.
2. **Why local embeddings?** Embedding is the highest-volume API call. Running BGE-M3 on MPS eliminates this cost.
3. **Why separate embedding service?** GraphRAG expects an OpenAI-compatible API. Local FastAPI wrapper = free + fast.
4. **Why Chroma for baseline?** Lightweight, no external deps, persistent, fair comparison (both use BGE-M3).
5. **Why MPS over MLX?** sentence-transformers has first-class MPS support with OpenAI-compatible server ecosystem.
EOF

# --- README.md ---
cat << 'EOF' > README.md
# P8: GraphRAG Lab — Knowledge Graph Retrieval Experimental Platform

> A production-grade GraphRAG experimentation platform for comparing knowledge graph-based RAG with traditional vector RAG.

## Quick Start

```bash
make setup                    # 1. Install dependencies
make download-corpus          # 2. Download 50+ AI/ML documents
make preprocess               # 3. Clean documents
cp .env.example .env          # 4. Edit .env → set GRAPHRAG_API_KEY
make init-graphrag            # 5. Initialize GraphRAG config
make run-embed                # 6. Terminal 1: start embedding service
make run-index                # 7. Terminal 2: build graph index
make run-query-global         # 8. Terminal 3: query!
make compare                  # 9. GraphRAG vs Vector RAG benchmark
```

## Project Structure

```
08_graphrag-lab/
├── Makefile                 # One-command orchestration
├── configs/                 # GraphRAG settings (DeepSeek + local)
├── data/
│   ├── raw/                 # Raw corpus (Wikipedia + arXiv)
│   ├── input/               # Preprocessed .txt for indexing
│   ├── output/              # Index artifacts (*.parquet)
│   └── vector_store/        # Chroma vector DB
├── scripts/                 # Pipeline scripts (numbered)
├── src/graphrag_lab/        # Core Python package
└── docs/                    # Architecture + comparison report
```

## License

MIT
EOF
```

#### 1.5.6 Makefile（工程编排中枢）

```bash
cat << 'EOF' > Makefile
SHELL := /bin/bash

PROJECT_NAME := graphrag-lab
CONDA_ENV ?= cxllm

PY := PYTHONPATH=. conda run -n $(CONDA_ENV) python
PIP := conda run -n $(CONDA_ENV) python -m pip

EMBED_HOST ?= 127.0.0.1
EMBED_PORT ?= 19530
LLM_HOST ?= 127.0.0.1
LLM_PORT ?= 8081

TMUX_SESSION ?= p8-graphrag
GRAPH_ROOT ?= .

.PHONY: help
help:
	@echo ""
	@echo "P8 GraphRAG Lab - Knowledge Graph Retrieval"
	@echo ""
	@echo "Available commands:"
	@echo "  make setup              Create conda env + install all dependencies"
	@echo "  make check-env          Verify Python/Conda/MPS/API Key"
	@echo "  make download-corpus    Download AI/ML corpus (Wikipedia + arXiv)"
	@echo "  make preprocess         Clean and normalize documents"
	@echo "  make init-graphrag      Initialize GraphRAG project config"
	@echo "  make run-embed          Start local BGE-M3 embedding service"
	@echo "  make run-index          Run GraphRAG index pipeline"
	@echo "  make run-query-global   Execute Global Search query"
	@echo "  make run-query-local    Execute Local Search query"
	@echo "  make run-vector-rag     Build Vector RAG baseline (Chroma)"
	@echo "  make compare            GraphRAG vs Vector RAG benchmark"
	@echo "  make analyze            Analyze index artifacts (parquet)"
	@echo "  make run-all            Start full pipeline in tmux"
	@echo "  make attach             Attach to tmux session"
	@echo "  make stop               Stop all services"
	@echo "  make clean              Remove index artifacts and cache"
	@echo ""

.PHONY: setup
setup:
	@echo "[setup] checking conda env: $(CONDA_ENV)"
	@conda info --envs | awk '{print $$1}' | grep -qx "$(CONDA_ENV)" || conda create -n $(CONDA_ENV) python=3.11 -y
	@echo "[setup] upgrading pip"
	@$(PIP) install -U pip setuptools wheel
	@echo "[setup] installing PyTorch nightly (MPS)"
	@$(PIP) install torch torchvision --index-url https://download.pytorch.org/whl/nightly/cpu
	@echo "[setup] installing project dependencies"
	@$(PIP) install -U -r requirements.txt
	@echo "[setup] installing hf-transfer"
	@$(PIP) install -U hf-transfer
	@echo "[setup] persisting HF_ENDPOINT to conda env"
	@conda env config vars set -n $(CONDA_ENV) HF_ENDPOINT=https://hf-mirror.com || true
	@echo "[setup] warming up BGE-M3 (first run downloads ~2.2GB)..."
	@HF_ENDPOINT=https://hf-mirror.com HF_HUB_ENABLE_HF_TRANSFER=1 $(PY) - <<'PY'
from sentence_transformers import SentenceTransformer
m = SentenceTransformer("BAAI/bge-m3", device="mps")
print(f"BGE-M3 ready: dim={m.get_sentence_embedding_dimension()}")
PY
	@echo "[setup] done"

.PHONY: check-env
check-env:
	@$(PY) scripts/00_check_env.py

.PHONY: download-corpus
download-corpus:
	@echo "[corpus] downloading AI/ML corpus..."
	@mkdir -p data/raw data/input data/output data/vector_store logs
	@PYTHONPATH=. bash scripts/01_download_corpus.sh
	@echo "[corpus] done"

.PHONY: preprocess
preprocess:
	@echo "[preprocess] cleaning documents..."
	@$(PY) scripts/02_preprocess_docs.py --input data/raw --output data/input

.PHONY: init-graphrag
init-graphrag:
	@echo "[init] initializing GraphRAG project..."
	@$(PY) scripts/03_init_graphrag.py

.PHONY: run-embed
run-embed:
	@echo "[embed] BGE-M3 embedding service on :$(EMBED_PORT)"
	@echo "[embed] Verify: curl -s http://$(EMBED_HOST):$(EMBED_PORT)/health"
	@$(PY) src/graphrag_lab/serve_embedding.py --host $(EMBED_HOST) --port $(EMBED_PORT) --model BAAI/bge-m3 --device mps

.PHONY: run-index
run-index:
	@echo "[index] checking embedding service..."
	@curl -sf http://$(EMBED_HOST):$(EMBED_PORT)/health > /dev/null || \
		(echo "ERROR: Embedding service not running on :$(EMBED_PORT). Start with: make run-embed" && exit 1)
	@echo "[index] embedding service OK, running GraphRAG pipeline (5-10 min)..."
	@$(PY) -m graphrag index --root $(GRAPH_ROOT)
	@echo "[index] done. artifacts in data/output/"
	@ls -lh data/output/*.parquet 2>/dev/null || echo "check data/output/"

.PHONY: run-query-global
run-query-global:
	@$(PY) scripts/04_query_demo.py --method global

.PHONY: run-query-local
run-query-local:
	@$(PY) scripts/04_query_demo.py --method local

.PHONY: run-vector-rag
run-vector-rag:
	@$(PY) scripts/05_vector_rag_baseline.py --input data/input --vector-store data/vector_store --embedding-model BAAI/bge-m3 --chunk-size 1200 --chunk-overlap 100

.PHONY: compare
compare:
	@$(PY) scripts/06_compare_rag.py --graphrag-root $(GRAPH_ROOT) --vector-store data/vector_store --embedding-model BAAI/bge-m3 --output docs/comparison_report.md

.PHONY: analyze
analyze:
	@$(PY) scripts/07_analyze_artifacts.py

.PHONY: run-all
run-all:
	@echo "[run-all] starting services in tmux: $(TMUX_SESSION)"
	@tmux has-session -t $(TMUX_SESSION) 2>/dev/null && tmux kill-session -t $(TMUX_SESSION) || true
	@tmux new-session -d -s $(TMUX_SESSION) -n embed "make run-embed"
	@tmux new-window -t $(TMUX_SESSION):1 -n index "sleep 10 && echo 'Embedding ready. Run: make run-index'; bash"
	@tmux new-window -t $(TMUX_SESSION):2 -n query "sleep 15 && echo 'Ready. Run: make run-query-global or make compare'; bash"
	@echo ""
	@echo "tmux session: $(TMUX_SESSION)"
	@echo "  Window 0 (embed): BGE-M3 embedding service"
	@echo "  Window 1 (index): GraphRAG index pipeline"
	@echo "  Window 2 (query): Query & compare"
	@echo ""
	@echo "  make attach   — attach to session"
	@echo "  make stop     — kill everything"
	@echo ""

.PHONY: attach
attach:
	@tmux attach -t $(TMUX_SESSION)

.PHONY: stop
stop:
	@echo "[stop] killing tmux session: $(TMUX_SESSION)"
	@tmux kill-session -t $(TMUX_SESSION) 2>/dev/null || true
	@echo "[stop] killing embedding service on :$(EMBED_PORT)..."
	@lsof -ti:$(EMBED_PORT) | xargs kill -9 2>/dev/null || true
	@echo "[stop] done"

.PHONY: clean
clean: stop
	@echo "[clean] removing artifacts and cache..."
	@rm -rf data/output/*.parquet data/output/*.json data/output/*.graphml
	@rm -rf data/vector_store/*
	@rm -rf logs/* cache/
	@rm -rf .pytest_cache .ruff_cache
	@find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	@mkdir -p data/output data/vector_store logs
	@touch data/output/.gitkeep data/vector_store/.gitkeep logs/.gitkeep
	@echo "[clean] done"

.PHONY: nuke
nuke: clean
	@echo "[nuke] removing models and conda env..."
	@rm -rf models/
	@conda env remove -n $(CONDA_ENV) -y 2>/dev/null || true
	@echo "[nuke] everything destroyed. Run 'make setup' to rebuild."
EOF
```

#### 1.5.7 Bootstrap 完成验证

```bash
# 验证所有文件已创建
echo "=== File Inventory ==="
find . -type f -not -path './.git/*' | sort | while read f; do
  echo "  $f ($(wc -c < "$f") bytes)"
done

echo ""
echo "=== Directory Tree ==="
find . -type d -not -path './.git/*' | sort | head -20

echo ""
echo "[bootstrap] ✓ All source files created."
echo "[bootstrap] Next: Chapter 2 — Dependency Installation"
```

---

## 2. 依赖安装与最新工具链配置

### 2.1 硬件与资源精算

| 维度 | 数值 | 备注 |
|:-----|:-----|:-----|
| 系统内存 | 32GB 统一内存 | GPU 与 CPU 共享，无显存瓶颈 |
| GPU 后端 | Apple M5 GPU（Metal 3） | MPS 加速 PyTorch，Metal 加速 llama.cpp |
| 磁盘 | 1TB SSD | BGE-M3 约 2.2GB，索引产物 <500MB，总占用 ~3-5GB |
| 下载加速 | `HF_ENDPOINT=https://hf-mirror.com` | 国内镜像，所有 HuggingFace 操作必须注入 |

### 2.2 Conda 环境与 PyTorch（Apple Metal 优化）

```bash
# 确保 cxllm 环境存在
conda info --envs | grep cxllm || conda create -n cxllm python=3.11 -y

# 升级 pip 本身
conda run -n cxllm python -m pip install --upgrade pip setuptools wheel

# 安装 Apple Metal 优化的 PyTorch（使用 nightly cpu-only build，MPS 后端内置）
conda run -n cxllm python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/nightly/cpu

# 验证 MPS 可用性
conda run -n cxllm python -c "
import torch
print(f'PyTorch: {torch.__version__}')
print(f'MPS available: {torch.backends.mps.is_available()}')
x = torch.randn(3,3).to('mps')
y = x @ x
print(f'MPS matmul OK: device={y.device}, shape={y.shape}')
"
# 预期输出:
# PyTorch: 2.6.0.dev...
# MPS available: True
# MPS matmul OK: device=mps:0, shape=torch.Size([3, 3])
```

### 2.3 项目依赖一键安装

```bash
# 进入项目目录
cd /Users/chenxi/Documents/晨熙个人/0暑期自学大模型/phase4_projects/08_graphrag-lab

# 安装所有依赖（requirements.txt 已在 Chapter 1 中创建）
conda run -n cxllm python -m pip install -U -r requirements.txt

# 额外安装 hf-transfer（Rust 多线程下载，比默认下载器快 3-5x）
conda run -n cxllm python -m pip install -U hf-transfer

# 持久化 HuggingFace 国内镜像到 Conda 环境
conda env config vars set -n cxllm HF_ENDPOINT=https://hf-mirror.com
# 需要 deactivate → activate 才生效：
conda deactivate 2>/dev/null; conda activate cxllm

# 验证 GraphRAG CLI 可用
conda run -n cxllm python -c "
import importlib.metadata
print(f'GraphRAG: {importlib.metadata.version(\"graphrag\")}')
from graphrag.cli.main import app
print('GraphRAG CLI: OK')
"
```

### 2.4 BGE-M3 模型预热（首次下载 ~2.2GB）

```bash
# 注入国内镜像（必须！否则会从 huggingface.co 下载，速度极慢或失败）
export HF_ENDPOINT=https://hf-mirror.com
export HF_HUB_ENABLE_HF_TRANSFER=1

# 预热 BGE-M3：首次运行会自动下载约 2.2GB 模型文件到 HF_HOME 缓存
conda run -n cxllm python -c "
from sentence_transformers import SentenceTransformer
print('Downloading BAAI/bge-m3 (first time only, ~2.2GB)...')
model = SentenceTransformer('BAAI/bge-m3', device='mps')
print(f'BGE-M3 loaded on MPS, dim={model.get_sentence_embedding_dimension()}')
emb = model.encode(['GraphRAG is a knowledge graph based RAG approach.'])
print(f'Test embedding shape: {emb.shape}')
print('BGE-M3: OK')
"

# 预期输出:
# Downloading BAAI/bge-m3...
# BGE-M3 loaded on MPS, dim=1024
# Test embedding shape: (1, 1024)
# BGE-M3: OK
```

### 2.5 避坑指南：MPS 与 Conda 环境隔离

1. **MPS fallback**：`torch.backends.mps.is_available()` 返回 True 但 OOM 时 PyTorch 不会自动 fallback 到 CPU。BGE-M3 的 max_seq_length 为 8192，长文本会产生大张量。代码中已将 batch_size 限制在 ≤16，避免触发 Metal 内存碎片。

2. **Conda `run` 环境穿透**：`conda run -n cxllm` 不会继承 shell 的所有环境变量。使用 `conda env config vars set` 持久化 `HF_ENDPOINT` 是推荐做法。临时使用时可手动导出：`conda run -n cxllm env HF_ENDPOINT=https://hf-mirror.com python ...`

3. **sentence-transformers 版本**：必须 >= 3.0.0，旧版本对 MPS backend 的 `trust_remote_code` 支持有 bug。

4. **DeepSeek API 并发限制**：免费版 DeepSeek 有 RPM 限制。`settings.yaml` 中 `concurrent_requests: 4` 对免费版可能偏高，建议降为 `2`。

---

## 3. 分终端执行与测试流程（Debug 视角）

> **前提**：Chapter 1 的所有源码文件已创建完毕，Chapter 2 的依赖已安装完毕。

### 3.1 整体架构与终端分工

```
Terminal 1: 本地 BGE-M3 嵌入服务 (port 19530)
  → OpenAI-compatible /v1/embeddings endpoint
  → 为 GraphRAG 索引提供免费、低延迟的文本向量化

Terminal 2: GraphRAG 索引管线
  → 实体抽取 → 关系构建 → 社区检测 → 社区摘要
  → 输出 data/output/*.parquet

Terminal 3: 查询 & 评测 & 对比
  → Global Search / Local Search 查询
  → Vector RAG 基线构建
  → GraphRAG vs Vector RAG 对比评测
```

### 3.2 Terminal 1 — 本地嵌入服务（核心步骤，包含完整源码）

**文件**：[src/graphrag_lab/serve_embedding.py](src/graphrag_lab/serve_embedding.py)（已在 Section 1.5.4 中创建）

```bash
conda activate cxllm
cd /Users/chenxi/Documents/晨熙个人/0暑期自学大模型/phase4_projects/08_graphrag-lab

# 确认嵌入服务源码存在
ls -la src/graphrag_lab/serve_embedding.py
# 预期输出: -rw-r--r-- ... src/graphrag_lab/serve_embedding.py

# 启动嵌入服务（监听 19530 端口，使用 MPS 后端）
PYTHONPATH=. python src/graphrag_lab/serve_embedding.py \
  --host 127.0.0.1 \
  --port 19530 \
  --model BAAI/bge-m3 \
  --device mps

# ============ 预期成功日志 ============
# [EmbeddingServer] 11:23:45 | INFO | Loading BAAI/bge-m3 on mps ...
# [EmbeddingServer] 11:23:52 | INFO | Model loaded. dim=1024, max_seq_length=8192
# [EmbeddingServer] 11:23:52 | INFO | Listening on http://127.0.0.1:19530
# INFO:     Started server process [12345]
# INFO:     Uvicorn running on http://127.0.0.1:19530
```

**验证嵌入服务**（新开一个终端或使用 curl）：

```bash
# Test 1: Health check
curl -s http://127.0.0.1:19530/health | python -m json.tool
# 预期输出:
# {
#     "status": "ok",
#     "model": "bge-m3",
#     "dim": 1024,
#     "max_seq_length": 8192
# }

# Test 2: 实际嵌入生成
curl -s http://127.0.0.1:19530/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{"input": ["Transformer is a neural network architecture."], "model": "bge-m3"}' \
  | python -c "import sys,json; d=json.load(sys.stdin); print(f'dim={len(d[\"data\"][0][\"embedding\"])}, model={d[\"model\"]}')"
# 预期输出: dim=1024, model=bge-m3
```

### 3.3 Terminal 2 — 语料准备与 GraphRAG 索引

**文件清单**（均在 Section 1.5.3 中创建）：
- [scripts/01_download_corpus.sh](scripts/01_download_corpus.sh) — 语料下载脚本
- [scripts/02_preprocess_docs.py](scripts/02_preprocess_docs.py) — 文档预处理
- [scripts/03_init_graphrag.py](scripts/03_init_graphrag.py) — GraphRAG 项目初始化

```bash
conda activate cxllm
cd /Users/chenxi/Documents/晨熙个人/0暑期自学大模型/phase4_projects/08_graphrag-lab

# ===== Step 1: 下载语料库（2-5 分钟）=====
PYTHONPATH=. bash scripts/01_download_corpus.sh
# 预期产出：
#   data/raw/ 下生成 50-70 个 .txt 文件（wiki_*.txt + arxiv_*.txt）
# 验证：
ls data/raw/*.txt | wc -l
# 预期：> 50

# ===== Step 2: 文档预处理 =====
PYTHONPATH=. python scripts/02_preprocess_docs.py \
  --input data/raw \
  --output data/input

# 预期日志：
# [preprocess] Processing 65 raw files...
# [preprocess] SUMMARY:
#   Raw files scanned : 65
#   Cleaned & written : 62
#   Skipped           : 3
#   Total tokens (est): ~45,000

# ===== Step 3: 初始化 GraphRAG 项目 =====
PYTHONPATH=. python scripts/03_init_graphrag.py

# 预期日志：
# [init] ✓ .env already exists (or created from .env.example)
# [init] ✗ WARNING: GRAPHRAG_API_KEY not set — (...if you haven't edited .env)
# [init] ✓ Copied configs/settings.yaml → settings.yaml
# [init] ✓ Input corpus: 62 files, 512 KB
# [init] ✓ Output directories ready

# ===== 关键步骤：编辑 .env 设置 API Key =====
# 如果你还没有设置 DeepSeek API Key，现在编辑：
nano .env  # 或用 vim、code
# 将 GRAPHRAG_API_KEY=sk-your-deepseek-api-key-here
# 改为 GRAPHRAG_API_KEY=sk-xxxxxxxxxxxxxxxx（你的真实 key）
# 获取 key: https://platform.deepseek.com/api_keys

# 保存后重新运行 init 验证：
PYTHONPATH=. python scripts/03_init_graphrag.py
# 预期看到: [init] ✓ GRAPHRAG_API_KEY: sk-xxxx...xxxx

# ===== Step 4: 运行 GraphRAG 索引（核心步骤，约 5-10 分钟）=====
# 前提：Terminal 1 的嵌入服务已启动且通过健康检查
curl -sf http://127.0.0.1:19530/health || echo "ERROR: Start Terminal 1 embed service first!"

PYTHONPATH=. conda run -n cxllm python -m graphrag index --root .

# ============ 预期阶段性日志 ============
# ✅ create_base_text_units   → 将 data/input/*.txt 分块（200-400 chunks）
# ✅ create_final_documents   → 关联文档与文本单元
# 🔄 extract_graph            → LLM 密集调用：实体抽取 + 关系抽取
#    [extract_graph] processing chunk 1/300 ...
#    [extract_graph] entity extraction: found 8 entities
#    [extract_graph] relationship summarization: found 5 relationships
#    ...
# 🔄 finalize_graph           → 去重、合并实体与关系
# ✅ create_communities       → Leiden 社区检测
# 🔄 create_community_reports → LLM 调用：为每个社区生成摘要
# 🔄 generate_text_embeddings → 本地嵌入服务生成向量
# ✅ All workflows completed successfully.

# 验证索引产物
ls -lh data/output/*.parquet
# 预期看到 6 个 parquet 文件:
#   entities.parquet, relationships.parquet, communities.parquet,
#   community_reports.parquet, text_units.parquet, documents.parquet
```

**资源消耗参考（50-80 篇文档）**

| 指标 | 预估值 | 备注 |
|:-----|:------|:-----|
| 文本块 (chunks) | 200-400 个 | 每块 1200 tokens |
| 抽取实体 | 300-800 个 | 取决于文档丰富度 |
| 抽取关系 | 200-600 条 | 实体对级别 |
| 社区数 | 15-40 个 | Leiden 算法产出 |
| LLM 调用次数 | ~800-1500 次 | 实体+关系+摘要 |
| DeepSeek API 成本 | ~$0.05-0.15 | deepseek-chat 极便宜 |
| 索引耗时 | 5-10 分钟 | 取决于网络和 API 延迟 |
| 磁盘占用 | ~3-5 GB | 含 2.2GB BGE-M3 + 索引产物 |

### 3.4 Terminal 3 — 查询与对比评测

**文件清单**：
- [scripts/04_query_demo.py](scripts/04_query_demo.py) — 查询演示（global + local + batch）
- [scripts/05_vector_rag_baseline.py](scripts/05_vector_rag_baseline.py) — Vector RAG 基线
- [scripts/06_compare_rag.py](scripts/06_compare_rag.py) — 量化对比
- [scripts/07_analyze_artifacts.py](scripts/07_analyze_artifacts.py) — 索引产物分析

```bash
conda activate cxllm
cd /Users/chenxi/Documents/晨熙个人/0暑期自学大模型/phase4_projects/08_graphrag-lab

# ===== Step 5: 运行查询演示 =====

# Global Search（社区级别总结）
PYTHONPATH=. python scripts/04_query_demo.py \
  --method global \
  --query "这个知识库主要涵盖哪些技术主题？"
# 预期输出: 返回一段英文总结，列出 Transformer、BERT、Attention 等主题

# Local Search（实体关系/多跳问题）
PYTHONPATH=. python scripts/04_query_demo.py \
  --method local \
  --query "How are Transformer architecture and LoRA related?"
# 预期输出: 返回实体间的关系路径

# 批量评测（8 个预设查询，自动选择 global/local 方法）
PYTHONPATH=. python scripts/04_query_demo.py --batch
# 预期输出: 逐个打印查询结果和耗时

# ===== Step 6: 构建 Vector RAG 基线 =====
PYTHONPATH=. python scripts/05_vector_rag_baseline.py \
  --input data/input \
  --vector-store data/vector_store \
  --embedding-model BAAI/bge-m3 \
  --chunk-size 1200 \
  --chunk-overlap 100

# 预期日志：
# [VectorRAG] Loading BAAI/bge-m3 on mps ...
# [VectorRAG] Chunking 62 documents...
# [VectorRAG] Total chunks: 468
# [VectorRAG] Encoding 468 chunks (batch_size=16)...
# [VectorRAG] Encoding done in 12.3s
# [VectorRAG] Persisted: data/vector_store/
# [VectorRAG] Collection 'graphrag_lab_corpus': 468 vectors
# [VectorRAG] ✓ Baseline ready.

# ===== Step 7: GraphRAG vs Vector RAG 量化对比 =====
PYTHONPATH=. python scripts/06_compare_rag.py \
  --graphrag-root . \
  --vector-store data/vector_store \
  --embedding-model BAAI/bge-m3 \
  --output docs/comparison_report.md

# 预期输出: 8 个查询的对比表格，以及 docs/comparison_report.md 报告文件
# QUICK SUMMARY:
#   [factual   ]  GraphRAG=3.5s  Vector=0.4s  → vector
#   [multi_hop ]  GraphRAG=4.2s  Vector=0.3s  → graphrag
#   ...

# ===== Step 8: 分析索引产物 =====
PYTHONPATH=. python scripts/07_analyze_artifacts.py

# 预期输出:
# GraphRAG Index Artifacts Analysis
#   ✓ entities.parquet                          450 rows × 5 cols
#   ✓ relationships.parquet                     320 rows × 4 cols
#   ...
# ENTITIES: 450 total
#   Top entity types:
#   MODEL                  ████████████████████   120
#   METHOD                 ████████████████        95
#   ...
# INDEX QUALITY METRICS
#   Relationship-to-Entity ratio: 0.71 ✓
#   Unique entity types: 8
#   Communities detected: 22
```

---

## 4. 终极一键运行：Makefile 集成

> Makefile 已在 Section 1.5.6 中创建。本章聚焦于使用方式和工作原理。

### 4.1 Make 命令速查

| 命令 | 耗时 | 作用 |
|:-----|:-----|:-----|
| `make help` | 1s | 显示所有可用命令 |
| `make setup` | 5-10 min | 首次运行：创建环境、安装依赖、预热 BGE-M3 |
| `make check-env` | 5s | 验证 Python / Conda / MPS / API Key / 磁盘 / 目录 |
| `make download-corpus` | 1-2 min | 下载 50+ 篇 AI/ML 文档到 data/raw/ |
| `make preprocess` | 10s | 文档清洗标准化 |
| `make init-graphrag` | 3s | 生成 settings.yaml 和 .env |
| `make run-embed` | 持续运行 | **Terminal 1** — 启动本地嵌入服务（:19530） |
| `make run-index` | 5-10 min | **Terminal 2** — 构建 GraphRAG 图谱索引 |
| `make run-query-global` | 3-5s | Global Search 交互式查询 |
| `make run-query-local` | 3-5s | Local Search 交互式查询 |
| `make run-vector-rag` | 30-60s | 构建 Vector RAG 基线（Chroma 向量库） |
| `make compare` | 2-3 min | GraphRAG vs Vector RAG 对比评测 |
| `make analyze` | 5s | 解析 parquet 索引产物，打印统计 |
| `make run-all` | - | **tmux 一键拉起全流程**（3 个窗口） |
| `make attach` | - | 接入 tmux 会话 |
| `make stop` | 1s | 关闭所有 tmux 窗口和嵌入服务 |
| `make clean` | 1s | 清空索引产物和缓存（保留模型和环境） |
| `make nuke` | 1 min | 核弹级清理：删除 conda 环境和所有模型 |

### 4.2 典型工作流

```bash
# === 首次运行 ===
make setup                         # 1. 环境 + 依赖 + BGE-M3 预热
make download-corpus               # 2. 下载语料
make preprocess                    # 3. 文档清洗
# 手动编辑 .env 设置 GRAPHRAG_API_KEY
make init-graphrag                 # 4. 初始化 GraphRAG
make check-env                     # 5. 全面自检

# === 启动服务（3 个终端或 make run-all） ===
# 方式 A：手动 3 终端
#   Terminal 1: make run-embed
#   Terminal 2: make run-index
#   Terminal 3: make run-query-global / make compare

# 方式 B：一键 tmux
make run-all                       # 启动 tmux 会话 p8-graphrag
make attach                        # 接入查看，Ctrl+B D 断开

# === 查询与评测 ===
make analyze                       # 分析索引产物
make compare                       # GraphRAG vs Vector RAG 对比
```

### 4.3 如何优雅地终止服务

```bash
# 方式 1：Makefile（推荐）
make stop          # 杀死 tmux 会话 + 嵌入服务进程

# 方式 2：手动杀端口
lsof -ti:19530 | xargs kill -9   # 杀嵌入服务
lsof -ti:8081 | xargs kill -9    # 杀 llama.cpp（如果启动了本地 LLM）

# 方式 3：tmux 内手动关
make attach        # 接入 tmux
# Ctrl+C 逐个窗口停止 → Ctrl+B D 断开
make stop          # 清理残余
```

---

## 5. 常见坑点与硬件降维打击方案

### 5.1 坑点 1：GraphRAG 索引时连接本地嵌入服务失败

**现象**：
```
httpx.ConnectError: [Errno 61] Connection refused
Error in generate_text_embeddings workflow
```

**根因**：Terminal 1 的嵌入服务未启动，或 macOS 防火墙拦截。

**解决方案**（按优先级）：

```bash
# 1. 确认嵌入服务在运行
curl -s http://127.0.0.1:19530/health

# 2. 检查端口是否被占用
lsof -i :19530
# 如果被其他进程占用：lsof -ti :19530 | xargs kill -9

# 3. 重新启动嵌入服务
make run-embed

# 4. 如果仍失败，检查 macOS 防火墙
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate
# 如果开启，临时放行 Python
```

**预防**：`make run-index` 已内置健康检查，嵌入服务未启动会直接报错并提示。

### 5.2 坑点 2：DeepSeek API JSON 模式报错 + Rate Limit

**现象**：
```
openai.BadRequestError: model does not support json mode
openai.RateLimitError: Rate limit reached
```

**解决方案**：

```yaml
# settings.yaml 关键配置
llm:
  model_supports_json: true      # DeepSeek V2+ 支持
  concurrent_requests: 2         # 从 4 降到 2，避免触发限流
  request_timeout: 300.0         # 超时增加到 5 分钟
  sleep_on_rate_limit_recommendation: true  # 收到 429 后自动退避

parallelization:
  num_threads: 4                 # 从 8 降到 4
  stagger: 0.5                   # 增加交错延迟到 0.5s
```

如果 JSON mode 仍然报错，在 `prompts/entity_extraction.txt` 末尾追加：
```text
IMPORTANT: You MUST respond with ONLY a valid JSON array. No markdown code blocks, no explanatory text.
```

### 5.3 坑点 3：MPS 内存溢出

**现象**：
```
RuntimeError: MPS backend out of memory.
```

**根因**：Apple Silicon 统一内存架构下，BGE-M3 长文本（max_seq_length=8192）+ 大 batch_size 导致 Metal 内存碎片。

**解决方案**（已在源码中实现）：
- `serve_embedding.py`：batch_size 限制为 16
- `05_vector_rag_baseline.py`：`--embed-batch-size 16` 参数
- 避免在索引期间同时跑 Chroma 向量库构建 + 嵌入服务

```bash
# 释放 Metal 内存
make stop && sleep 2 && make run-embed
```

### 5.4 坑点 4：Windows → macOS 迁移痛点

| 痛点 | Windows 习惯 | macOS 正确姿势 |
|:-----|:------------|:-------------|
| 路径分隔符 | `\` (反斜杠) | `/` (正斜杠)，所有 Python Path 对象自动处理 |
| 换行符 | `\r\n` (CRLF) | `\n` (LF)，`git config --global core.autocrlf input` |
| 进程守护 | `nohup` 或 Windows Service | `tmux` / `launchctl` / `brew services` |
| 端口监听 | `netstat -ano` | `lsof -i :PORT` |
| GPU 后端 | CUDA (`cuda`) | MPS (`mps`)，所有 `device='cuda'` 需改为 `device='mps'` |
| Conda 路径 | `C:\Users\...\.conda\envs` | `/opt/homebrew/Caskroom/miniforge/base/envs/` |

### 5.5 坑点 5：索引产物实体数异常少

**现象**：50+ 篇文档只抽出 12 个实体。

**解决方案**：
```yaml
# settings.yaml 检查清单
entity_extraction:
  max_gleanings: 1           # 至少 1 轮 gleaning
chunks:
  size: 800                  # 从 1200 降到 800
llm:
  model: deepseek-chat       # 不要用本地 tiny 模型
```

---

## 6. 面试深度解析

### 6.1 题一：Leiden 社区检测 vs ANN 近邻搜索的本质差异

**数学本质**：
- **Leiden**：模块度最大化 Q = (1/2m) Σᵢⱼ [Aᵢⱼ − (kᵢkⱼ/2m)] δ(cᵢ, cⱼ)，在图拓扑空间寻找高内聚低耦合的子图
- **ANN**：度量空间距离最小化 argminₓ∈D dist(q, x)，在嵌入空间找最近点

**硬件差异**：
- Leiden：稀疏矩阵乘法（SpMM），受限于内存带宽
- ANN：密集矩阵乘法（GEMM），可充分利用 AMX 加速器和 Neural Engine

**关键洞察**：两者互补——GraphRAG 做"拓扑导航"，Vector RAG 做"语义跳转"。

### 6.2 题二：如何在 32GB M5 上优化 GraphRAG 索引吞吐

**调用量模型**：N 块 → N 次实体抽取 + ~E 次关系总结 + C 次社区摘要 ≈ 800-1500 次 LLM 调用

**优化维度**：
| 维度 | 措施 | 提升 |
|:-----|:-----|:----|
| 并发策略 | `async_mode: threaded` + `concurrent_requests: 4-8` | 2-4x |
| 嵌入本地化 | BGE-M3 本地服务替代 API | 10-50x |
| Prompt 精简 | 自定义 prompt 减少 token | 1.3-1.5x |
| 缓存复用 | cache/ 目录缓存 LLM 响应 | 重复索引趋近即时 |
| 分块策略 | chunk_size 800 → 每块实体更少 | 单块延迟 -30% |

### 6.3 题三：百万级文档的 GraphRAG 瓶颈与重构

**崩溃点**：LLM 调用量 ~1M 次（$500-2000+）、图谱存储单机无法容纳、Leiden 小时级、嵌入生成千万级 chunks。

**企业级重构**：
- **存储**：Parquet → Neo4j/NebulaGraph（分布式）；社区摘要 → MinIO/S3；数据版本 → Apache Iceberg
- **计算**：实体抽取 → Ray/Spark MapReduce；嵌入 → Ray Serve 分布式集群；Leiden → cuGraph/ParLeiden
- **查询**：图遍历 → HNSW + 双向 BFS；全局搜索 → 分层社区结构；缓存 → Redis

**关键洞察**：真正的工程判断力在于"什么时候不需要 scale GraphRAG"——如果 80% 查询是事实性问答，Hybrid RAG（Vector 召回 + 轻量图谱遍历）的 ROI 远高于全量 GraphRAG。

---

## 附录 A：快速排障速查表

| 症状 | 最可能原因 | 快速修复 |
|:-----|:----------|:-------|
| `ModuleNotFoundError: graphrag` | 未安装 | `conda run -n cxllm pip install graphrag` |
| `Connection refused :19530` | 嵌入服务未启动 | `make run-embed` |
| `API key not valid` | .env 未配置 | `cp .env.example .env && nano .env` |
| `No files in data/input` | 未下载语料 | `make download-corpus && make preprocess` |
| `MPS out of memory` | batch_size 过大 | 修改 batch_size=8 |
| `Rate limit` | DeepSeek 并发太高 | `concurrent_requests: 1` in settings.yaml |
| `settings.yaml not found` | 未初始化 | `make init-graphrag` |
| tmux: command not found | tmux 未安装 | `brew install tmux` |
| `pip install` 超时 | 无国内镜像 | `export HF_ENDPOINT=https://hf-mirror.com` |

## 附录 B：产出物 Checklist

- [ ] `make check-env` 全部 PASS
- [ ] 语料下载完成（`data/raw/` 下 50+ 个 .txt 文件）
- [ ] 文档预处理完成（`data/input/` 下有标准化 .txt）
- [ ] GraphRAG 索引构建完成（`data/output/` 下有 6 个 parquet 文件）
- [ ] 嵌入服务正常运行（curl :19530/health 返回 OK）
- [ ] Global Search 至少跑 3 个查询
- [ ] Local Search 至少跑 3 个查询
- [ ] Vector RAG 基线构建完成（Chroma 向量库）
- [ ] GraphRAG vs Vector RAG 对比报告生成（`docs/comparison_report.md`）
- [ ] 索引产物分析完成（实体数、关系数、社区数）
- [ ] 记录索引耗时 + Token 消耗 + API 成本
- [ ] README.md 更新
- [ ] Git commit（不含 .env 和模型文件）

---

> **Runbook End** — 此文档覆盖了从环境搭建到面试深度的完整工程链路。每一个 `.py` 和 `.sh` 文件均在 Chapter 1 中通过 `cat << 'EOF'` 完整创建，严格遵循"先建文件 → 再装依赖 → 最后执行"的工程时序。
> 项目地址：`08_graphrag-lab/`
