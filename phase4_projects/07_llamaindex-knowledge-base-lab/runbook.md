# P7: LlamaIndex 知识库应用工程 Runbook（Day 65–67）

> **核心价值**：掌握 LlamaIndex 核心抽象（Document → Node → Index → QueryEngine），构建可本地运行、可持久化、可多知识库路由的现代 RAG 系统。
>
> **硬件基线**：MacBook Air M5 / 32GB Unified Memory / 1TB SSD / macOS Sequoia
>
> **环境隔离**：Conda 虚拟环境 `cxllm`，Python 3.11
>
> **最终产物**：
> - VectorStoreIndex 语义检索 + SummaryIndex 全文总结
> - RouterQueryEngine 多知识库自动路由
> - IngestionPipeline 文档摄取流水线（分块 → 元数据抽取 → 嵌入）
> - 本地 BGE Embedding 模型 + ChromaDB 向量持久化
> - 完整 Makefile 自动化 + tmux 多终端管理
> - GitHub 可直接开箱克隆的项目结构

---

# 1. 工程化目录架构

## 1.1 目录树设计

```
07_llamaindex-knowledge-base-lab/
│
├── configs/                  # YAML 全局配置（模型、路径、超参）
│   ├── settings.yaml         #   运行时主配置
│   └── model_config.yaml     #   Embedding / LLM 模型参数
│
├── data/                     # 数据三层分离
│   ├── raw/                  #   原始文档（Markdown/PDF/TXT，只读不写）
│   ├── processed/            #   清洗/分块后的中间产物
│   └── vector_store/         #   ChromaDB 持久化向量库
│
├── docs/                     # 项目文档
│   ├── architecture.md       #   架构决策记录（ADR）
│   └── comparison_report.md  #   LlamaIndex vs LangChain 对比报告
│
├── scripts/                  # Shell 自动化脚本
│   ├── download_models.sh    #   从 HF 镜像下载 Embedding 模型
│   ├── setup_env.sh          #   一键初始化 Conda 环境
│   ├── ingest.sh             #   文档摄取流水线
│   └── query.sh              #   交互式查询启动
│
├── src/                      # 核心源码（按职责拆分）
│   ├── loaders/              #   文档加载器（本地/Notion/GitHub 连接器）
│   │   └── document_loader.py
│   ├── ingestion/            #   摄取管道（分块 + 元数据抽取）
│   │   └── pipeline.py
│   ├── indexes/              #   索引构建（Vector / Summary / Keyword）
│   │   ├── build_vector_index.py
│   │   └── build_summary_index.py
│   ├── query_engines/        #   查询引擎封装（含流式输出 & 引用溯源）
│   │   ├── base.py
│   │   ├── vector_query.py
│   │   └── summary_query.py
│   ├── routers/              #   多知识库路由器
│   │   └── multi_kb_router.py
│   └── utils/                #   工具函数（日志、配置解析、MPS 检测）
│       ├── config.py
│       └── device.py
│
├── tests/                    # 单元测试
│   ├── test_ingestion.py
│   ├── test_indexes.py
│   └── test_router.py
│
├── logs/                     # 运行时日志（gitignore）
├── storage/                  # LlamaIndex 索引持久化目录（gitignore）
│
├── Makefile                  # 一键自动化（setup / build / query / clean）
├── requirements.txt          # Python 依赖清单
├── README.md                 # 项目说明
└── .gitignore                # Git 忽略规则
```

## 1.2 各目录工程作用（一句话）

| 目录 | 工程作用 |
| :--- | :--- |
| `configs/` | 集中管理运行时参数，消除硬编码，支持多环境切换 |
| `data/raw/` | 原始文档的不可变存储层，作为数据溯源的唯一真相源 |
| `data/processed/` | 清洗/分块后的中间产物，避免重复计算 |
| `data/vector_store/` | ChromaDB 嵌入向量持久化，实现索引与查询进程分离 |
| `docs/` | 架构决策与对比报告，供面试官/协作者理解设计意图 |
| `scripts/` | Shell 自动化入口，降低小白上手门槛 |
| `src/loaders/` | 多源文档连接器抽象层，支持本地/Notion/GitHub 扩展 |
| `src/ingestion/` | 文档摄取管道：分块策略 + 元数据富化 |
| `src/indexes/` | 索引构建逻辑，每种 Index 类型独立模块 |
| `src/query_engines/` | 查询引擎封装，统一 query/retrieve 接口 |
| `src/routers/` | 多知识库路由决策层，LLM 驱动的语义分发 |
| `src/utils/` | 横切关注点：配置加载、设备检测、日志 |
| `tests/` | 单元测试，保障管道/索引/路由核心逻辑正确性 |
| `logs/` | 运行时日志集中输出，便于 `tail -f` 实时监控 |
| `storage/` | LlamaIndex 原生索引持久化，与向量库互补 |

## 1.3 一键初始化命令

```bash
# 进入 Phase4 项目根目录
cd /Users/chenxi/Documents/晨熙个人/0暑期自学大模型/phase4_projects

# 创建带编号的主目录及完整子目录树
mkdir -p 07_llamaindex-knowledge-base-lab/{configs,data/{raw,processed,vector_store},docs,scripts,src/{loaders,ingestion,indexes,query_engines,routers,utils},tests,logs,storage}

# 进入项目目录
cd 07_llamaindex-knowledge-base-lab

# 创建顶层空文件
touch README.md requirements.txt Makefile .gitignore runbook.md

# 创建子目录占位文件（防止 Git 忽略空目录）
touch configs/.gitkeep data/raw/.gitkeep data/processed/.gitkeep data/vector_store/.gitkeep
touch docs/.gitkeep scripts/.gitkeep src/loaders/.gitkeep src/ingestion/.gitkeep
touch src/indexes/.gitkeep src/query_engines/.gitkeep src/routers/.gitkeep
touch src/utils/.gitkeep tests/.gitkeep logs/.gitkeep storage/.gitkeep

# 验证目录结构
find . -type d | sort
```

---

# 2. 依赖安装与最新工具链配置

## 2.1 确认 Conda 环境

```bash
conda activate cxllm
python --version   # 预期：Python 3.11.x
which python       # 预期：/Users/chenxi/miniconda3/envs/cxllm/bin/python
```

若 `cxllm` 环境不存在，先创建：

```bash
conda create -n cxllm python=3.11 -y
conda activate cxllm
```

## 2.2 HuggingFace 国内镜像（强保底）

```bash
# 会话级生效
export HF_ENDPOINT=https://hf-mirror.com

# 永久生效（写入 .zshrc）
echo 'export HF_ENDPOINT=https://hf-mirror.com' >> ~/.zshrc
source ~/.zshrc

# 验证镜像连通性
curl -s -o /dev/null -w "%{http_code}" https://hf-mirror.com
# 预期输出：200
```

## 2.3 requirements.txt

```bash
cat << 'EOF' > requirements.txt
# ============================================================
# P7: LlamaIndex 知识库应用 — 依赖清单
# 平台：macOS Sequoia / Apple Silicon M5 / Python 3.11
# ============================================================

# --- LlamaIndex 核心 ---
llama-index-core>=0.12.0
llama-index>=0.12.0

# --- 向量存储后端 ---
llama-index-vector-stores-chroma>=0.4.0
chromadb>=0.5.0

# --- Embedding 模型支持 ---
llama-index-embeddings-huggingface>=0.3.0
sentence-transformers>=3.0.0

# --- LLM 后端 ---
llama-index-llms-openai>=0.3.0
openai>=1.50.0

# --- 文档读取器 ---
llama-index-readers-file>=0.3.0

# --- 元数据抽取器 ---
llama-index-extractors>=0.1.0

# --- PyTorch (Apple Silicon MPS 加速) ---
torch>=2.5.0
transformers>=4.45.0

# --- 工具库 ---
accelerate>=1.0.0
pydantic>=2.0.0
pyyaml>=6.0
rich>=13.0.0
tqdm>=4.66.0
click>=8.0.0
EOF
```

## 2.4 Apple Silicon MPS 加速安装

```bash
# 升级 pip 工具链
pip install -U pip setuptools wheel

# 安装全部依赖（pip 会自动选择 Apple Silicon 兼容的 wheel）
pip install -r requirements.txt

# 若下载慢，追加国内 PyPI 镜像：
# pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 2.5 MPS 加速验证 + 硬件信息确认

```bash
python -c "
import torch
import sys

print(f'Python:       {sys.version}')
print(f'PyTorch:      {torch.__version__}')
print(f'MPS built:    {torch.backends.mps.is_built()}')
print(f'MPS available:{torch.backends.mps.is_available()}')

if torch.backends.mps.is_available():
    # 验证 MPS 张量运算
    x = torch.randn(2, 3, device='mps')
    y = torch.randn(3, 2, device='mps')
    z = x @ y
    print(f'MPS matmul:   {z.shape} ✓')
else:
    print('⚠️  MPS 不可用，检查 PyTorch 是否为 arm64 版本')
"
# 预期输出：
# Python:       3.11.x
# PyTorch:      2.5.x
# MPS built:    True
# MPS available:True
# MPS matmul:   torch.Size([2, 2]) ✓
```

## 2.6 验证关键包的版本一致性

```bash
python -c "
import llama_index.core
import chromadb
import sentence_transformers
print(f'llama-index-core:       {llama_index.core.__version__}')
print(f'chromadb:               {chromadb.__version__}')
print(f'sentence-transformers:  {sentence_transformers.__version__}')
"
```

---

# 3. 源码完整实现

> **以下每个源码文件均使用 `cat << 'EOF' >` 格式，复制到终端回车即可一键生成。**

## 3.1 配置文件

### configs/settings.yaml

```bash
cat << 'EOF' > configs/settings.yaml
# ============================================================
# P7 LlamaIndex Lab — 运行时主配置
# ============================================================

# --- Embedding 模型 ---
embedding:
  model_name: "BAAI/bge-small-zh-v1.5"
  device: "mps"               # Apple Silicon MPS 加速
  normalize: true
  max_length: 512

# --- LLM 配置 ---
llm:
  provider: "openai"
  model: "gpt-4o-mini"
  temperature: 0.0
  max_tokens: 1024
  # API Key 从环境变量 OPENAI_API_KEY 读取，不硬编码

# --- 索引配置 ---
index:
  persist_dir: "storage"
  similarity_top_k: 5
  chunk_size: 500
  chunk_overlap: 50
  embed_batch_size: 32

# --- 向量库配置 (ChromaDB) ---
vector_store:
  persist_dir: "data/vector_store"
  collection_name: "llamaindex_kb"

# --- 数据路径 ---
data:
  raw_dir: "data/raw"
  processed_dir: "data/processed"

# --- 日志配置 ---
logging:
  level: "INFO"
  file: "logs/llamaindex.log"
EOF
```

### configs/model_config.yaml

```bash
cat << 'EOF' > configs/model_config.yaml
# ============================================================
# P7 LlamaIndex Lab — 模型参数配置
# ============================================================

# BGE Small Chinese v1.5 — 专为中文优化的轻量 Embedding 模型
bge_small_zh:
  model_name: "BAAI/bge-small-zh-v1.5"
  dim: 512                    # 输出向量维度
  max_seq_length: 512
  size_mb: 130                # 模型文件大小
  pooling: "mean"             # 池化策略：mean pooling
  instruction_prefix: "为这个句子生成表示以用于检索相关文章："

# GPT-4o-mini — 性价比最优的问答 LLM
gpt4o_mini:
  model_name: "gpt-4o-mini"
  context_window: 128000
  max_output_tokens: 16384
  cost_per_1k_input: 0.00015  # USD
  cost_per_1k_output: 0.0006  # USD
EOF
```

## 3.2 .gitignore

```bash
cat << 'EOF' > .gitignore
# ============================================================
# P7 LlamaIndex Lab — Git 忽略规则
# ============================================================

# Python
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/
.eggs/

# 环境
.env
*.env

# 模型文件（体积大，不纳入版本控制）
models/
*.bin
*.safetensors
*.pth
*.pt

# 索引持久化 & 向量库（运行时产物）
storage/
data/vector_store/
data/processed/

# 日志
logs/*.log

# 系统文件
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
*.swp
*.swo

# Conda
.miniconda/
miniconda3/

# Jupyter
.ipynb_checkpoints/
EOF
```

## 3.3 工具模块

### src/utils/device.py — MPS 设备检测

```bash
cat << 'EOF' > src/utils/device.py
"""Apple Silicon MPS 设备检测与内存监控."""

import torch
import platform
import subprocess


def detect_device() -> str:
    """检测最优可用设备，优先 MPS。

    Returns:
        "mps" / "cuda" / "cpu"
    """
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def get_memory_info() -> dict:
    """获取统一内存使用情况（仅 macOS）。

    Returns:
        {"total_gb": float, "used_gb": float, "pressure": str}
    """
    if platform.system() != "Darwin":
        return {"total_gb": 0, "used_gb": 0, "pressure": "unknown"}

    try:
        result = subprocess.run(
            ["vm_stat"], capture_output=True, text=True, timeout=5
        )
        # 解析 vm_stat 输出获取内存压力
        lines = result.stdout.strip().split("\n")
        info = {}
        for line in lines:
            if ":" in line:
                key, val = line.split(":", 1)
                val = val.strip().rstrip(".")
                try:
                    info[key.strip()] = int(val)
                except ValueError:
                    pass

        page_size = 16384  # Apple Silicon 页大小 16KB
        free_pages = info.get("Pages free", 0)
        total_pages = sum(
            v for k, v in info.items()
            if k in ("Pages free", "Pages active", "Pages inactive",
                      "Pages speculative", "Pages wired down")
        )
        used_pages = total_pages - free_pages
        total_gb = (total_pages * page_size) / (1024**3)
        used_gb = (used_pages * page_size) / (1024**3)

        # 简化压力判断
        ratio = used_pages / total_pages if total_pages > 0 else 0
        if ratio < 0.5:
            pressure = "normal"
        elif ratio < 0.75:
            pressure = "warning"
        else:
            pressure = "critical"

        return {"total_gb": round(total_gb, 1), "used_gb": round(used_gb, 1), "pressure": pressure}
    except Exception:
        return {"total_gb": 32.0, "used_gb": 0, "pressure": "unknown"}


def print_device_info():
    """打印设备信息摘要。"""
    device = detect_device()
    print(f"Compute Device : {device.upper()}")

    if device == "mps":
        print(f"PyTorch MPS    : built={torch.backends.mps.is_built()}, "
              f"available={torch.backends.mps.is_available()}")

    mem = get_memory_info()
    print(f"Unified Memory : {mem['total_gb']} GB total, {mem['used_gb']} GB used")
    print(f"Memory Pressure: {mem['pressure']}")
EOF
```

### src/utils/config.py — YAML 配置加载器

```bash
cat << 'EOF' > src/utils/config.py
"""YAML 配置加载器，支持嵌套键访问."""

import os
import yaml
from pathlib import Path
from typing import Any


class Config:
    """配置管理器，支持点号路径访问嵌套键。

    用法：
        cfg = Config.load("configs/settings.yaml")
        model = cfg.get("embedding.model_name")
    """

    def __init__(self, data: dict):
        self._data = data

    @classmethod
    def load(cls, path: str) -> "Config":
        """从 YAML 文件加载配置。"""
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if data is None:
            raise ValueError(f"配置文件为空: {path}")
        return cls(data)

    def get(self, key_path: str, default: Any = None) -> Any:
        """通过点号路径获取配置值。

        Args:
            key_path: 点号分隔的键路径，如 "embedding.model_name"
            default: 默认值

        Returns:
            配置值
        """
        keys = key_path.split(".")
        value = self._data
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        return value

    def to_dict(self) -> dict:
        """返回原始配置字典。"""
        return self._data


def get_project_root() -> Path:
    """获取项目根目录绝对路径。"""
    return Path(__file__).resolve().parent.parent.parent


def ensure_dir(path: str) -> Path:
    """确保目录存在，不存在则创建。

    Args:
        path: 相对于项目根目录的路径

    Returns:
        目录的绝对 Path 对象
    """
    full_path = get_project_root() / path
    full_path.mkdir(parents=True, exist_ok=True)
    return full_path
EOF
```

## 3.4 文档加载器

### src/loaders/document_loader.py

```bash
cat << 'EOF' > src/loaders/document_loader.py
"""多源文档加载器：支持本地 Markdown/PDF/TXT 目录递归加载."""

from pathlib import Path
from typing import List, Optional

from llama_index.core import SimpleDirectoryReader
from llama_index.core.schema import Document
from rich.console import Console

console = Console()


def load_local_documents(
    input_dir: str = "data/raw",
    recursive: bool = True,
    required_exts: Optional[List[str]] = None,
    exclude_hidden: bool = True,
) -> List[Document]:
    """从本地目录递归加载文档。

    Args:
        input_dir: 文档目录路径（相对于项目根目录或绝对路径）
        recursive: 是否递归子目录
        required_exts: 限定文件扩展名，默认 [".md", ".txt", ".pdf", ".rst"]
        exclude_hidden: 是否排除隐藏文件

    Returns:
        Document 对象列表
    """
    if required_exts is None:
        required_exts = [".md", ".txt", ".pdf", ".rst", ".html"]

    # 解析路径：支持相对路径和绝对路径
    dir_path = Path(input_dir)
    if not dir_path.is_absolute():
        from src.utils.config import get_project_root
        dir_path = get_project_root() / input_dir

    if not dir_path.exists():
        raise FileNotFoundError(
            f"文档目录不存在: {dir_path}\n"
            f"请先创建目录并放入文档：mkdir -p {dir_path}"
        )

    console.print(f"[bold blue]📂 扫描文档目录: {dir_path}[/bold blue]")

    reader = SimpleDirectoryReader(
        input_dir=str(dir_path),
        recursive=recursive,
        required_exts=required_exts,
        exclude_hidden=exclude_hidden,
    )

    documents = reader.load_data()

    console.print(f"[green]✅ 加载完成: {len(documents)} 个文档[/green]")
    for doc in documents[:5]:
        preview = doc.text[:80].replace("\n", " ")
        console.print(f"   📄 {doc.metadata.get('file_name', '?')} | {preview}...")
    if len(documents) > 5:
        console.print(f"   ... 及其他 {len(documents) - 5} 个文档")

    return documents


def get_document_stats(documents: List[Document]) -> dict:
    """统计文档基本信息。

    Returns:
        {"total_docs": int, "total_chars": int, "extensions": dict}
    """
    total_chars = sum(len(doc.text) for doc in documents)
    exts = {}
    for doc in documents:
        fn = doc.metadata.get("file_name", "unknown")
        ext = Path(fn).suffix or ".unknown"
        exts[ext] = exts.get(ext, 0) + 1

    return {
        "total_docs": len(documents),
        "total_chars": total_chars,
        "extensions": exts,
    }
EOF
```

## 3.5 摄取管道

### src/ingestion/pipeline.py

```bash
cat << 'EOF' > src/ingestion/pipeline.py
"""文档摄取管道：分块 → 元数据抽取 → 嵌入.

使用 LlamaIndex IngestionPipeline 将原始 Document 列表转化为
带 Embedding 和元数据的 Node 列表，支持缓存以避免重复计算。
"""

import hashlib
import json
from pathlib import Path
from typing import List, Optional

from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import BaseNode, Document
from llama_index.core.extractors import (
    TitleExtractor,
    QuestionsAnsweredExtractor,
)
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from rich.console import Console
from rich.progress import Progress

from src.utils.config import Config, ensure_dir

console = Console()


def build_ingestion_pipeline(
    config: Config,
    embedding_model: Optional[HuggingFaceEmbedding] = None,
) -> IngestionPipeline:
    """构建文档摄取管道。

    Pipeline 顺序：
        1. SentenceSplitter   — 按语义边界分块
        2. TitleExtractor      — LLM 提取标题
        3. QuestionsAnsweredExtractor — LLM 生成"这段回答什么问题"
        4. HuggingFaceEmbedding — 向量嵌入

    Args:
        config: 配置对象
        embedding_model: 可选的外部嵌入模型（复用可节省显存）

    Returns:
        配置好的 IngestionPipeline 实例
    """
    chunk_size = config.get("index.chunk_size", 500)
    chunk_overlap = config.get("index.chunk_overlap", 50)

    if embedding_model is None:
        embedding_model = HuggingFaceEmbedding(
            model_name=config.get("embedding.model_name", "BAAI/bge-small-zh-v1.5"),
            device=config.get("embedding.device", "mps"),
            max_length=config.get("embedding.max_length", 512),
        )

    transformations = [
        SentenceSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            paragraph_separator="\n\n",
        ),
        TitleExtractor(
            llm=None,  # 使用全局 Settings.llm
            nodes=5,   # 每个文档取前5个节点生成标题
        ),
        QuestionsAnsweredExtractor(
            llm=None,  # 使用全局 Settings.llm
            questions=3,  # 每个节点生成3个问题
        ),
        embedding_model,
    ]

    pipeline = IngestionPipeline(transformations=transformations)

    console.print(
        f"[bold blue]🔧 摄取管道配置:[/bold blue]\n"
        f"   chunk_size={chunk_size}, chunk_overlap={chunk_overlap}\n"
        f"   embedding={config.get('embedding.model_name')}"
    )

    return pipeline


def run_ingestion(
    documents: List[Document],
    pipeline: Optional[IngestionPipeline] = None,
    config: Optional[Config] = None,
    cache_dir: str = "data/processed",
) -> List[BaseNode]:
    """执行文档摄取，生成 Nodes。

    Args:
        documents: 原始 Document 列表
        pipeline: 可选的预配置管道，不传则自动构建
        config: 配置对象（pipeline 为空时必需）
        cache_dir: 缓存目录，避免重复摄取

    Returns:
        BaseNode 列表（含 Embedding + Metadata）
    """
    if config is None:
        config = Config.load("configs/settings.yaml")

    # 计算文档哈希，用于缓存检测
    doc_hash = _compute_docs_hash(documents)
    cache_path = Path(cache_dir) / f"nodes_{doc_hash}.json"

    if cache_path.exists():
        console.print(f"[yellow]⚠️  发现缓存: {cache_path.name}，跳过摄取[/yellow]")
        # 注意：从缓存恢复 Node 需要反序列化，此处简化处理
        console.print("[yellow]   如需强制重建请删除 data/processed/ 目录[/yellow]")

    if pipeline is None:
        pipeline = build_ingestion_pipeline(config)

    ensure_dir(cache_dir)

    console.print(f"[bold blue]🚀 开始摄取 {len(documents)} 个文档...[/bold blue]")

    with Progress() as progress:
        task = progress.add_task("[cyan]摄取中...", total=len(documents))
        nodes = pipeline.run(documents=documents, show_progress=True)

    # 保存节点元数据到缓存
    nodes_meta = [
        {"node_id": n.node_id, "text_len": len(n.text), "metadata": n.metadata}
        for n in nodes
    ]
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(nodes_meta, f, ensure_ascii=False, indent=2)

    console.print(
        f"[green]✅ 摄取完成: {len(documents)} 文档 → {len(nodes)} 个节点[/green]"
    )
    for node in nodes[:3]:
        preview = node.text[:100].replace("\n", " ")
        meta_keys = list(node.metadata.keys()) if node.metadata else []
        console.print(f"   📦 {preview}... | meta={meta_keys}")

    return nodes


def _compute_docs_hash(documents: List[Document]) -> str:
    """计算文档列表的内容哈希。"""
    hasher = hashlib.sha256()
    for doc in sorted(documents, key=lambda d: d.doc_id or ""):
        hasher.update((doc.doc_id or "").encode())
        hasher.update(doc.text[:200].encode())  # 仅用前200字符加速
    return hasher.hexdigest()[:12]
EOF
```

## 3.6 索引构建

### src/indexes/build_vector_index.py

```bash
cat << 'EOF' > src/indexes/build_vector_index.py
#!/usr/bin/env python3
"""VectorStoreIndex 构建器：语义向量索引.

使用 ChromaDB 作为持久化向量后端，BGE Embedding 模型生成中文语义向量。
"""

import sys
from pathlib import Path

# 确保项目根目录在 sys.path 中
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from llama_index.core import (
    VectorStoreIndex,
    Settings,
    StorageContext,
)
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from rich.console import Console
import chromadb

from src.utils.config import Config, ensure_dir
from src.utils.device import detect_device, print_device_info
from src.loaders.document_loader import load_local_documents, get_document_stats

console = Console()


def main():
    """构建 VectorStoreIndex 主流程。"""
    console.print("[bold magenta]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold magenta]")
    console.print("[bold magenta]  VectorStoreIndex 构建器[/bold magenta]")
    console.print("[bold magenta]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold magenta]")

    # 1. 打印设备信息
    print_device_info()

    # 2. 加载配置
    config = Config.load("configs/settings.yaml")
    device = detect_device()

    # 3. 配置全局 Settings
    Settings.embed_model = HuggingFaceEmbedding(
        model_name=config.get("embedding.model_name", "BAAI/bge-small-zh-v1.5"),
        device=device,
        max_length=config.get("embedding.max_length", 512),
    )
    console.print(f"[blue]🔌 Embedding 模型: {config.get('embedding.model_name')} on {device}[/blue]")

    # 4. 加载文档
    documents = load_local_documents(input_dir=config.get("data.raw_dir", "data/raw"))
    if not documents:
        console.print("[red]❌ 未找到文档！请将 .md/.txt/.pdf 放入 data/raw/ 目录[/red]")
        sys.exit(1)

    stats = get_document_stats(documents)
    console.print(f"[blue]📊 文档统计: {stats['total_docs']} 个, {stats['total_chars']:,} 字符[/blue]")

    # 5. 初始化 ChromaDB 向量存储
    ensure_dir(config.get("vector_store.persist_dir", "data/vector_store"))
    chroma_client = chromadb.PersistentClient(
        path=config.get("vector_store.persist_dir", "data/vector_store")
    )

    collection_name = config.get("vector_store.collection_name", "llamaindex_kb")
    # 如果 collection 已存在则复用，否则创建
    try:
        chroma_collection = chroma_client.get_collection(collection_name)
        console.print(f"[yellow]⚠️  复用已存在的 ChromaDB Collection: {collection_name}[/yellow]")
    except Exception:
        chroma_collection = chroma_client.create_collection(collection_name)
        console.print(f"[green]✅ 创建 ChromaDB Collection: {collection_name}[/green]")

    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    # 6. 构建索引
    console.print("[bold blue]🔨 构建 VectorStoreIndex（这可能需要几分钟）...[/bold blue]")
    index = VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        embed_batch_size=config.get("index.embed_batch_size", 32),
        show_progress=True,
    )

    # 7. 持久化 LlamaIndex 索引元数据（与 ChromaDB 数据互补）
    persist_dir = config.get("index.persist_dir", "storage")
    ensure_dir(persist_dir)
    index.storage_context.persist(persist_dir=persist_dir)

    console.print(f"[green]✅ VectorStoreIndex 构建完成[/green]")
    console.print(f"[green]   LlamaIndex 索引 → {persist_dir}/[/green]")
    console.print(f"[green]   ChromaDB 向量  → {config.get('vector_store.persist_dir')}/[/green]")

    return index


if __name__ == "__main__":
    main()
EOF
```

### src/indexes/build_summary_index.py

```bash
cat << 'EOF' > src/indexes/build_summary_index.py
#!/usr/bin/env python3
"""SummaryIndex 构建器：全文总结索引.

适合"总结全文"、"概括要点"类非精确检索任务。
与 VectorStoreIndex 互补，分别覆盖语义搜索和全文聚合场景。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from llama_index.core import SummaryIndex, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from rich.console import Console

from src.utils.config import Config
from src.utils.device import detect_device
from src.loaders.document_loader import load_local_documents

console = Console()


def main():
    """构建 SummaryIndex 主流程。"""
    console.print("[bold magenta]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold magenta]")
    console.print("[bold magenta]  SummaryIndex 构建器[/bold magenta]")
    console.print("[bold magenta]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold magenta]")

    config = Config.load("configs/settings.yaml")
    device = detect_device()

    Settings.embed_model = HuggingFaceEmbedding(
        model_name=config.get("embedding.model_name", "BAAI/bge-small-zh-v1.5"),
        device=device,
    )

    documents = load_local_documents(input_dir=config.get("data.raw_dir", "data/raw"))
    if not documents:
        console.print("[red]❌ 未找到文档[/red]")
        sys.exit(1)

    console.print("[bold blue]🔨 构建 SummaryIndex...[/bold blue]")
    summary_index = SummaryIndex.from_documents(
        documents,
        show_progress=True,
    )

    console.print("[green]✅ SummaryIndex 构建完成[/green]")
    console.print("[yellow]💡 提示：SummaryIndex 不适合精确检索，请用于总结类查询[/yellow]")

    return summary_index


if __name__ == "__main__":
    main()
EOF
```

## 3.7 查询引擎

### src/query_engines/base.py

```bash
cat << 'EOF' > src/query_engines/base.py
"""查询引擎基类：定义统一的查询接口."""

from abc import ABC, abstractmethod
from typing import List, Optional

from llama_index.core.schema import NodeWithScore


class BaseQueryEngine(ABC):
    """查询引擎抽象基类。

    所有查询引擎必须实现 query() 方法。
    """

    @abstractmethod
    def query(self, question: str) -> str:
        """执行查询并返回回答文本。

        Args:
            question: 用户问题

        Returns:
            回答文本
        """
        ...

    def query_with_sources(self, question: str) -> dict:
        """查询并附带来源信息。

        Args:
            question: 用户问题

        Returns:
            {"answer": str, "sources": List[dict]}
        """
        raise NotImplementedError


def format_sources(source_nodes: List[NodeWithScore]) -> str:
    """格式化引用来源为可读文本。

    Args:
        source_nodes: 检索到的源节点列表

    Returns:
        格式化的来源文本
    """
    lines = ["\n📎 引用来源:"]
    for i, node in enumerate(source_nodes, 1):
        score = node.score or 0.0
        file_name = node.metadata.get("file_name", "unknown")
        preview = node.text[:60].replace("\n", " ")
        lines.append(f"  [{i}] [{score:.2f}] {file_name} | {preview}...")
    return "\n".join(lines)
EOF
```

### src/query_engines/vector_query.py

```bash
cat << 'EOF' > src/query_engines/vector_query.py
#!/usr/bin/env python3
"""VectorStoreIndex 查询引擎：语义检索 + 流式输出 + 来源引用.

支持：
- 从持久化存储加载索引
- 交互式 REPL 查询
- 流式输出（逐 token 打印）
- 来源引用展示
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from llama_index.core import (
    Settings,
    StorageContext,
    load_index_from_storage,
)
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.vector_stores.chroma import ChromaVectorStore
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
import chromadb

from src.utils.config import Config
from src.utils.device import detect_device

console = Console()


def load_index(config: Config):
    """从持久化存储加载 VectorStoreIndex。

    同时加载 LlamaIndex 索引元数据（storage/）和 ChromaDB 向量数据（data/vector_store/）。
    """
    # 1. 连接 ChromaDB
    chroma_client = chromadb.PersistentClient(
        path=config.get("vector_store.persist_dir", "data/vector_store")
    )
    collection_name = config.get("vector_store.collection_name", "llamaindex_kb")
    chroma_collection = chroma_client.get_collection(collection_name)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

    # 2. 重建 StorageContext
    storage_context = StorageContext.from_defaults(
        persist_dir=config.get("index.persist_dir", "storage"),
        vector_store=vector_store,
    )

    # 3. 加载索引
    index = load_index_from_storage(storage_context)
    console.print(f"[green]✅ 索引加载成功[/green]")
    return index


def main():
    """交互式查询 REPL。"""
    console.print("[bold magenta]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold magenta]")
    console.print("[bold magenta]  VectorStoreIndex 查询引擎[/bold magenta]")
    console.print("[bold magenta]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold magenta]")

    config = Config.load("configs/settings.yaml")
    device = detect_device()

    # 配置全局 Settings
    Settings.embed_model = HuggingFaceEmbedding(
        model_name=config.get("embedding.model_name", "BAAI/bge-small-zh-v1.5"),
        device=device,
    )
    Settings.llm = OpenAI(
        model=config.get("llm.model", "gpt-4o-mini"),
        temperature=config.get("llm.temperature", 0.0),
    )

    # 加载索引
    index = load_index(config)

    # 创建查询引擎
    query_engine = index.as_query_engine(
        similarity_top_k=config.get("index.similarity_top_k", 5),
        streaming=True,
        response_mode="compact",
    )

    console.print("[bold green]💬 输入问题开始查询，输入 'exit' 退出[/bold green]")
    console.print("[dim]   提示：Ctrl+C 退出[/dim]\n")

    while True:
        try:
            question = console.input("[bold cyan]❯ [/bold cyan]")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]👋 再见！[/yellow]")
            break

        if not question.strip():
            continue
        if question.strip().lower() in ("exit", "quit", "q"):
            console.print("[yellow]👋 再见！[/yellow]")
            break

        # 执行查询
        console.print("[dim]⏳ 检索中...[/dim]")
        response = query_engine.query(question)

        # 流式输出回答
        console.print(Panel(
            Markdown(str(response)),
            title="🤖 回答",
            border_style="green",
        ))

        # 来源展示
        if hasattr(response, "source_nodes") and response.source_nodes:
            console.print("\n[bold]📎 引用来源:[/bold]")
            for i, node in enumerate(response.source_nodes[:5], 1):
                score = node.score or 0.0
                file_name = node.metadata.get("file_name", "unknown")
                preview = node.text[:100].replace("\n", " ")
                console.print(
                    f"  [{i}] [cyan]score={score:.3f}[/cyan] "
                    f"[dim]{file_name}[/dim] | {preview}..."
                )
        console.print()


if __name__ == "__main__":
    main()
EOF
```

### src/query_engines/summary_query.py

```bash
cat << 'EOF' > src/query_engines/summary_query.py
#!/usr/bin/env python3
"""SummaryIndex 查询引擎：全文总结模式.

与 VectorStoreIndex 的"精准检索 + TopK 上下文"不同，
SummaryIndex 采用"树状聚合（Tree Summarize）"策略，
遍历全部节点后逐级汇聚，适合回答全局性问题。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from llama_index.core import Settings, SummaryIndex
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.openai import OpenAI
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from src.utils.config import Config
from src.utils.device import detect_device
from src.loaders.document_loader import load_local_documents

console = Console()


def main():
    console.print("[bold magenta]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold magenta]")
    console.print("[bold magenta]  SummaryIndex 全文总结查询[/bold magenta]")
    console.print("[bold magenta]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold magenta]")

    config = Config.load("configs/settings.yaml")
    device = detect_device()

    Settings.embed_model = HuggingFaceEmbedding(
        model_name=config.get("embedding.model_name", "BAAI/bge-small-zh-v1.5"),
        device=device,
    )
    Settings.llm = OpenAI(
        model=config.get("llm.model", "gpt-4o-mini"),
        temperature=0.0,
    )

    # 实时构建 SummaryIndex（也可从持久化加载）
    documents = load_local_documents(input_dir=config.get("data.raw_dir", "data/raw"))
    summary_index = SummaryIndex.from_documents(documents)

    query_engine = summary_index.as_query_engine(
        response_mode="tree_summarize",
        streaming=True,
    )

    console.print("[bold green]💬 输入问题（建议：总结/概括/全文性问题），输入 'exit' 退出[/bold green]\n")

    while True:
        try:
            question = console.input("[bold yellow]❯ [/bold yellow]")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]👋 再见！[/yellow]")
            break

        if question.strip().lower() in ("exit", "quit", "q"):
            break

        console.print("[dim]⏳ 总结中（遍历全部节点）...[/dim]")
        response = query_engine.query(question)

        console.print(Panel(
            Markdown(str(response)),
            title="📝 总结（Tree Summarize）",
            border_style="yellow",
        ))
        console.print()


if __name__ == "__main__":
    main()
EOF
```

## 3.8 多知识库路由器

### src/routers/multi_kb_router.py

```bash
cat << 'EOF' > src/routers/multi_kb_router.py
#!/usr/bin/env python3
"""RouterQueryEngine 多知识库自动路由.

核心设计：
  用户问题 → LLM 语义解析 → 选择目标知识库 → 精准检索 → 生成回答

支持场景：
  - 技术笔记库 vs 论文库
  - 产品文档库 vs API 参考库
  - 中文内容库 vs 英文内容库
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from llama_index.core import (
    Settings,
    VectorStoreIndex,
)
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core.query_engine import RouterQueryEngine
from llama_index.core.selectors import LLMSingleSelector
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.openai import OpenAI
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.utils.config import Config
from src.utils.device import detect_device
from src.loaders.document_loader import load_local_documents

console = Console()


def create_knowledge_base(
    config: Config,
    data_subdir: str,
    name: str,
    description: str,
) -> QueryEngineTool:
    """创建单个知识库并包装为 QueryEngineTool。

    Args:
        config: 全局配置
        data_subdir: data/raw 下的子目录名
        name: 知识库名称（用于路由决策的 key）
        description: 知识库内容描述（LLM 用它做路由决策，务必精确）

    Returns:
        包装好的 QueryEngineTool
    """
    raw_dir = f"{config.get('data.raw_dir', 'data/raw')}/{data_subdir}"
    documents = load_local_documents(input_dir=raw_dir)

    if not documents:
        console.print(f"[yellow]⚠️  知识库 '{name}' 无文档，目录: {raw_dir}[/yellow]")

    index = VectorStoreIndex.from_documents(documents)
    query_engine = index.as_query_engine(
        similarity_top_k=config.get("index.similarity_top_k", 5),
    )

    tool = QueryEngineTool(
        query_engine=query_engine,
        metadata=ToolMetadata(
            name=name,
            description=description,
        ),
    )
    console.print(f"[green]✅ 知识库 '{name}' 就绪: {len(documents)} 个文档[/green]")
    return tool


def main():
    console.print("[bold magenta]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold magenta]")
    console.print("[bold magenta]  RouterQueryEngine 多知识库路由器[/bold magenta]")
    console.print("[bold magenta]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold magenta]")

    config = Config.load("configs/settings.yaml")
    device = detect_device()

    # 全局配置
    Settings.embed_model = HuggingFaceEmbedding(
        model_name=config.get("embedding.model_name", "BAAI/bge-small-zh-v1.5"),
        device=device,
    )
    Settings.llm = OpenAI(
        model=config.get("llm.model", "gpt-4o-mini"),
        temperature=0.0,
    )

    # 创建多个知识库
    # 🔑 关键：description 必须足够具体，否则 LLM 容易选错
    console.print("\n[bold blue]🔧 构建知识库...[/bold blue]")

    tool_notes = create_knowledge_base(
        config=config,
        data_subdir="notes",
        name="tech_notes",
        description=(
            "包含 Transformer、Attention 机制、KV Cache、RoPE 位置编码、"
            "MoE 混合专家模型、LoRA 微调、RLHF 对齐等大模型核心技术的学习笔记。"
            "适用问题：基础概念解释、技术原理、架构设计。"
        ),
    )

    tool_papers = create_knowledge_base(
        config=config,
        data_subdir="papers",
        name="academic_papers",
        description=(
            "包含学术论文：Attention is All You Need、LoRA: Low-Rank Adaptation、"
            "DPO: Direct Preference Optimization。"
            "适用问题：论文方法、损失函数推导、实验结果、数学公式。"
        ),
    )

    # 创建路由器
    router = RouterQueryEngine(
        selector=LLMSingleSelector.from_defaults(),
        query_engine_tools=[tool_notes, tool_papers],
        verbose=True,
    )

    # 展示路由表
    table = Table(title="🗺️ 路由表")
    table.add_column("知识库", style="cyan")
    table.add_column("名称", style="green")
    table.add_column("适用场景", style="dim")
    table.add_row("tech_notes", "技术笔记", "基础概念、技术原理")
    table.add_row("academic_papers", "学术论文", "论文方法、数学推导")
    console.print(table)

    console.print("\n[bold green]💬 输入问题测试自动路由，输入 'exit' 退出[/bold green]")
    console.print("[dim]   Router 会自动选择最合适的知识库来回答[/dim]\n")

    while True:
        try:
            question = console.input("[bold cyan]❯ [/bold cyan]")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]👋 再见！[/yellow]")
            break

        if question.strip().lower() in ("exit", "quit", "q"):
            break

        console.print("[dim]🧭 路由决策中...[/dim]")
        response = router.query(question)

        # 显示元数据：路由到了哪个知识库
        tool_name = response.metadata.get("tool_name", "unknown") if response.metadata else "unknown"

        console.print(Panel(
            str(response),
            title=f"🤖 回答 [路由: {tool_name}]",
            border_style="green" if tool_name != "unknown" else "red",
        ))
        console.print()


if __name__ == "__main__":
    main()
EOF
```

## 3.9 Shell 脚本

### scripts/download_models.sh

```bash
cat << 'EOF' > scripts/download_models.sh
#!/usr/bin/env bash
# ============================================================
# P7: 模型下载脚本 — 通过 HF 镜像下载 BGE Embedding 模型
# 平台：macOS / Apple Silicon
# ============================================================

set -euo pipefail

# --- 强制使用国内镜像 ---
export HF_ENDPOINT=https://hf-mirror.com

MODEL_NAME="BAAI/bge-small-zh-v1.5"
LOCAL_DIR="models/bge-small-zh-v1.5"

echo "============================================"
echo " P7 模型下载工具"
echo " 镜像: ${HF_ENDPOINT}"
echo " 模型: ${MODEL_NAME}"
echo " 本地: ${LOCAL_DIR}"
echo "============================================"

# 检查 hf 是否已安装
if ! command -v hf &> /dev/null; then
    echo "❌ hf 未安装，请先执行: pip install -U huggingface_hub[hf]"
    exit 1
fi

# 创建目标目录
mkdir -p "${LOCAL_DIR}"

echo ""
echo "🚀 开始下载模型..."
hf download \
    "${MODEL_NAME}" \
    --local-dir "${LOCAL_DIR}"

echo ""
echo "✅ 下载完成！模型文件:"
ls -lh "${LOCAL_DIR}/"
du -sh "${LOCAL_DIR}/"

echo ""
echo "💡 下一步: python src/indexes/build_vector_index.py"
EOF

chmod +x scripts/download_models.sh
```

### scripts/setup_env.sh

```bash
cat << 'EOF' > scripts/setup_env.sh
#!/usr/bin/env bash
# ============================================================
# P7: 环境一键初始化脚本
# ============================================================

set -euo pipefail

echo "============================================"
echo " P7 环境初始化"
echo " Conda 环境: cxllm"
echo " Python:     3.11"
echo "============================================"

# 1. 激活 Conda 环境
echo ""
echo "🔧 激活 Conda 环境 cxllm..."
# 注意：脚本中 conda activate 需要 source conda.sh
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate cxllm

echo "✅ Python $(python --version 2>&1)"

# 2. 设置 HF 镜像
export HF_ENDPOINT=https://hf-mirror.com
echo "✅ HF_ENDPOINT=${HF_ENDPOINT}"

# 3. 升级 pip
echo ""
echo "🔧 升级 pip 工具链..."
pip install -U pip setuptools wheel -q

# 4. 安装依赖
echo ""
echo "🔧 安装 Python 依赖..."
pip install -r requirements.txt

# 5. 验证关键包
echo ""
echo "🔧 验证安装..."
python -c "
import torch
import llama_index.core
import chromadb
print(f'PyTorch:        {torch.__version__}')
print(f'LlamaIndex:     {llama_index.core.__version__}')
print(f'ChromaDB:       {chromadb.__version__}')
print(f'MPS Available:  {torch.backends.mps.is_available()}')
"

echo ""
echo "============================================"
echo " ✅ 环境初始化完成"
echo "============================================"
echo ""
echo "下一步:"
echo "  1. bash scripts/download_models.sh   # 下载模型"
echo "  2. make build                         # 构建索引"
echo "  3. make query                         # 开始查询"
EOF

chmod +x scripts/setup_env.sh
```

### scripts/ingest.sh

```bash
cat << 'EOF' > scripts/ingest.sh
#!/usr/bin/env bash
# ============================================================
# P7: 文档摄取脚本
# ============================================================

set -euo pipefail

source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate cxllm

export HF_ENDPOINT=https://hf-mirror.com

echo "🚀 启动文档摄取..."
python -c "
from src.utils.config import Config
from src.loaders.document_loader import load_local_documents
from src.ingestion.pipeline import build_ingestion_pipeline, run_ingestion

config = Config.load('configs/settings.yaml')
docs = load_local_documents(input_dir='data/raw')
pipeline = build_ingestion_pipeline(config)
nodes = run_ingestion(docs, pipeline, config)
print(f'Done: {len(nodes)} nodes')
"
EOF

chmod +x scripts/ingest.sh
```

### scripts/query.sh

```bash
cat << 'EOF' > scripts/query.sh
#!/usr/bin/env bash
# ============================================================
# P7: 查询入口
# ============================================================

set -euo pipefail

source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate cxllm

export HF_ENDPOINT=https://hf-mirror.com

MODE="${1:-vector}"

case "$MODE" in
    vector)
        python src/query_engines/vector_query.py
        ;;
    summary)
        python src/query_engines/summary_query.py
        ;;
    router)
        python src/routers/multi_kb_router.py
        ;;
    *)
        echo "用法: bash scripts/query.sh [vector|summary|router]"
        echo "  vector  — VectorStoreIndex 语义检索（默认）"
        echo "  summary — SummaryIndex 全文总结"
        echo "  router  — RouterQueryEngine 多知识库路由"
        ;;
esac
EOF

chmod +x scripts/query.sh
```

## 3.10 单元测试

### tests/test_ingestion.py

```bash
cat << 'EOF' > tests/test_ingestion.py
"""摄取管道单元测试."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from llama_index.core.schema import Document

from src.ingestion.pipeline import build_ingestion_pipeline, _compute_docs_hash
from src.utils.config import Config


class TestIngestionPipeline:
    """测试 IngestionPipeline 核心逻辑。"""

    @pytest.fixture
    def config(self):
        return Config.load("configs/settings.yaml")

    @pytest.fixture
    def sample_docs(self):
        return [
            Document(text="Transformer 是一种基于注意力机制的神经网络架构。"),
            Document(text="LoRA 通过低秩分解实现参数高效微调。"),
        ]

    def test_pipeline_creation(self, config):
        """测试管道创建不报错。"""
        pipeline = build_ingestion_pipeline(config)
        assert pipeline is not None
        assert len(pipeline.transformations) >= 2

    def test_docs_hash_deterministic(self, sample_docs):
        """测试文档哈希的确定性。"""
        h1 = _compute_docs_hash(sample_docs)
        h2 = _compute_docs_hash(sample_docs)
        assert h1 == h2

    def test_docs_hash_changes_with_content(self, sample_docs):
        """测试内容变化导致哈希变化。"""
        h1 = _compute_docs_hash(sample_docs)
        sample_docs[0].text = "不同的内容"
        h2 = _compute_docs_hash(sample_docs)
        assert h1 != h2
EOF
```

### tests/test_indexes.py

```bash
cat << 'EOF' > tests/test_indexes.py
"""索引构建单元测试."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from llama_index.core import Settings, VectorStoreIndex, SummaryIndex
from llama_index.core.schema import Document
from llama_index.embeddings.huggingface import HuggingFaceEmbedding


class TestIndexBuilders:
    """测试索引构建逻辑。"""

    @pytest.fixture(autouse=True)
    def setup_embed_model(self):
        """注入轻量嵌入模型（避免测试中下载模型）。"""
        # 使用最简单的嵌入模型用于测试
        Settings.embed_model = HuggingFaceEmbedding(
            model_name="BAAI/bge-small-zh-v1.5",
            device="cpu",
        )

    @pytest.fixture
    def sample_docs(self):
        return [
            Document(text="Transformer 的核心是 Self-Attention 机制。"),
            Document(text="KV Cache 用于加速自回归生成。"),
            Document(text="RoPE 是一种旋转位置编码方法。"),
        ]

    def test_vector_index_build(self, sample_docs):
        """测试 VectorStoreIndex 构建成功。"""
        index = VectorStoreIndex.from_documents(sample_docs)
        assert index is not None

    def test_vector_index_query(self, sample_docs):
        """测试 VectorStoreIndex 基本查询。"""
        index = VectorStoreIndex.from_documents(sample_docs)
        engine = index.as_query_engine(similarity_top_k=2)
        response = engine.query("什么是 Self-Attention？")
        assert response is not None
        assert len(str(response)) > 0

    def test_summary_index_build(self, sample_docs):
        """测试 SummaryIndex 构建成功。"""
        index = SummaryIndex.from_documents(sample_docs)
        assert index is not None

    def test_summary_index_query(self, sample_docs):
        """测试 SummaryIndex 总结查询。"""
        index = SummaryIndex.from_documents(sample_docs)
        engine = index.as_query_engine(response_mode="tree_summarize")
        response = engine.query("总结这些内容")
        assert response is not None
        assert len(str(response)) > 0
EOF
```

### tests/test_router.py

```bash
cat << 'EOF' > tests/test_router.py
"""多知识库路由单元测试."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from llama_index.core import Settings, VectorStoreIndex
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core.query_engine import RouterQueryEngine
from llama_index.core.selectors import LLMSingleSelector
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.schema import Document


class TestRouter:
    """测试 RouterQueryEngine 路由决策。"""

    @pytest.fixture(autouse=True)
    def setup(self):
        Settings.embed_model = HuggingFaceEmbedding(
            model_name="BAAI/bge-small-zh-v1.5",
            device="cpu",
        )

    def test_router_creation(self):
        """测试路由器创建。"""
        tool_a = QueryEngineTool(
            query_engine=VectorStoreIndex.from_documents(
                [Document(text="内容 A")]
            ).as_query_engine(),
            metadata=ToolMetadata(
                name="tool_a",
                description="包含 Transformer 和 Attention 的学习笔记",
            ),
        )
        tool_b = QueryEngineTool(
            query_engine=VectorStoreIndex.from_documents(
                [Document(text="内容 B")]
            ).as_query_engine(),
            metadata=ToolMetadata(
                name="tool_b",
                description="包含 LoRA 和 DPO 的学术论文",
            ),
        )

        router = RouterQueryEngine(
            selector=LLMSingleSelector.from_defaults(),
            query_engine_tools=[tool_a, tool_b],
        )
        assert router is not None
        assert len(router._metadatas) == 2
EOF
```

---

# 4. 分终端执行与测试流程（Debug 视角）

## 4.1 终端拓扑图

```
┌─────────────────────────────────────────────────────┐
│  Terminal 1 (构建层)                                 │
│  conda activate cxllm                                │
│  make download    # 下载模型                          │
│  make build       # 构建索引                          │
│                                                      │
│  预期输出:                                            │
│  ✅ 加载 5 个文档                                     │
│  ✅ VectorStoreIndex 构建完成                          │
│  ✅ ChromaDB 持久化成功                                │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  Terminal 2 (查询层)                                 │
│  conda activate cxllm                                │
│  make query      # 启动交互式查询                      │
│                                                      │
│  ❯ 什么是 Transformer？                              │
│  🤖 Transformer 是一种基于 Self-Attention...          │
│  📎 [1] score=0.92 notes/transformer.md               │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  Terminal 3 (监控层)                                 │
│  # 监控日志                                           │
│  tail -f logs/llamaindex.log                          │
│                                                      │
│  # 监控内存                                           │
│  watch -n 2 'vm_stat | head -20'                      │
│                                                      │
│  # 监控进程                                           │
│  ps aux | grep python                                 │
└─────────────────────────────────────────────────────┘
```

## 4.2 Terminal 1 — 构建层详细步骤

```bash
# === 步骤 1：进入项目并激活环境 ===
cd /Users/chenxi/Documents/晨熙个人/0暑期自学大模型/phase4_projects/07_llamaindex-knowledge-base-lab
conda activate cxllm

# === 步骤 2：验证环境 ===
export HF_ENDPOINT=https://hf-mirror.com
python -c "import torch; print('MPS:', torch.backends.mps.is_available())"
# 预期：MPS: True

# === 步骤 3：下载模型（约 130MB，首次执行） ===
make download

# 预期输出：
# 🚀 开始下载模型...
# Downloading (in progress)...
# ✅ 下载完成！模型文件:
# -rw-r--r--  config.json
# -rw-r--r--  pytorch_model.bin (130MB)
# ...

# === 步骤 4：放入测试文档 ===
# 创建一些测试用的 Markdown 文档
cat << 'EOF' > data/raw/transformer_basics.md
# Transformer 基础

## Self-Attention 机制
Self-Attention 是 Transformer 的核心组件。它允许每个位置直接关注序列中的所有位置。

计算公式：Attention(Q,K,V) = softmax(QK^T / sqrt(d_k)) * V

## Multi-Head Attention
多头注意力通过并行运行多个 Self-Attention 来捕获不同子空间的信息。

## KV Cache
KV Cache 是一种推理优化技术，通过缓存 Key 和 Value 矩阵避免重复计算。
在自回归生成中，每步只需计算新 token 的 Query，复用之前的 K、V。
EOF

cat << 'EOF' > data/raw/lora_paper_summary.md
# LoRA: Low-Rank Adaptation of Large Language Models

## 核心思想
LoRA 通过在预训练权重旁添加低秩分解矩阵来实现参数高效微调。

## 数学表达
h = W_0 * x + B * A * x
其中 B ∈ R^{d×r}, A ∈ R^{r×k}, r << min(d,k)

## 优势
- 参数量减少 10000 倍
- 无推理延迟增加
- 可插拔式任务切换
EOF

cat << 'EOF' > data/raw/rope_explanation.md
# RoPE: 旋转位置编码

## 原理
RoPE 通过旋转矩阵将位置信息编码到 token 的表示中。

## 特点
- 相对位置编码，能捕捉 token 间的相对距离
- 与 Attention 机制天然兼容
- 支持长序列外推

## 数学形式
f(q, m) = q * e^{imθ}
f(k, n) = k * e^{inθ}
EOF

# === 步骤 5：构建索引 ===
make build

# 预期输出：
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   VectorStoreIndex 构建器
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Compute Device : MPS
# PyTorch MPS    : built=True, available=True
# Unified Memory : 32.0 GB total, X.X GB used
# Memory Pressure: normal
# 🔌 Embedding 模型: BAAI/bge-small-zh-v1.5 on mps
# 📂 扫描文档目录: .../data/raw
# ✅ 加载完成: 3 个文档
# 📊 文档统计: 3 个, XXXX 字符
# ✅ 创建 ChromaDB Collection: llamaindex_kb
# 🔨 构建 VectorStoreIndex（这可能需要几分钟）...
# ✅ VectorStoreIndex 构建完成
#    LlamaIndex 索引 → storage/
#    ChromaDB 向量  → data/vector_store/
```

## 4.3 Terminal 2 — 查询层交互

```bash
cd /Users/chenxi/Documents/晨熙个人/0暑期自学大模型/phase4_projects/07_llamaindex-knowledge-base-lab
conda activate cxllm

make query
```

预期交互过程：

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  VectorStoreIndex 查询引擎
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 索引加载成功
💬 输入问题开始查询，输入 'exit' 退出

❯ 什么是 KV Cache？

⏳ 检索中...
┌─ 🤖 回答 ─────────────────────────────┐
│ KV Cache 是一种大模型推理优化技术。      │
│                                          │
│ 在自回归生成过程中，模型每次只生成一个   │
│ token。传统方式每次都要重新计算所有历史  │
│ token 的 Key 和 Value 矩阵。KV Cache 通  │
│ 过缓存这些计算结果，使得每个新 token 只  │
│ 需计算自己的 K、V，避免了 O(n²) 的重复   │
│ 计算量。                                 │
│                                          │
│ 这可以将推理延迟降低 50%-70%，在现代     │
│ LLM 推理引擎（vLLM、TGI）中被广泛使用。  │
└──────────────────────────────────────────┘

📎 引用来源:
  [1] score=0.923 transformer_basics.md | # KV Cache...
  [2] score=0.856 rope_explanation.md | ## 特点...

❯ exit
👋 再见！
```

## 4.4 Terminal 3 — 监控层

```bash
# 实时监控应用日志
cd /Users/chenxi/Documents/晨熙个人/0暑期自学大模型/phase4_projects/07_llamaindex-knowledge-base-lab
tail -f logs/llamaindex.log

# 另开窗口监控统一内存压力
watch -n 2 'echo "=== Memory ===" && vm_stat | head -15 && echo "=== Processes ===" && ps aux | grep python | grep -v grep'
```

## 4.5 模型体积与硬件承载精算

| 资产 | 磁盘占用 | 内存占用（峰值） | 备注 |
| :--- | :--- | :--- | :--- |
| BGE-Small-ZH-v1.5 (pytorch_model.bin) | ~130 MB | ~500 MB | 512 维，MPS 加载后占用 |
| BGE-Small-ZH-v1.5 (其他文件) | ~10 MB | — | config.json, tokenizer 等 |
| ChromaDB 向量索引 (100 篇文档) | ~50 MB | ~200 MB | HNSW 索引 + 元数据 |
| ChromaDB 向量索引 (1000 篇文档) | ~500 MB | ~500 MB | 线性增长 |
| LlamaIndex 索引元数据 | ~10 MB | — | JSON 格式 |
| PyTorch + 依赖库 | ~3 GB | ~500 MB | 共享库共享内存 |
| Python 运行时 | — | ~200 MB | 基础开销 |
| **总计（100 篇文档基线）** | **~3.2 GB** | **~1.9 GB** | ✅ 32GB 完全无压力 |
| **总计（1000 篇文档基线）** | **~3.7 GB** | **~2.2 GB** | ✅ 32GB 仍有余量 |

> **结论**：M5 统一内存 32GB 对于本项目的 ChromaDB + BGE Embedding + LlamaIndex 全栈，即使是 10,000 篇文档的规模也能从容应对。真正的瓶颈在 LLM API 延迟而非本地计算。

---

# 5. 终极一键运行：Makefile 集成

## 5.1 完整 Makefile 源码

```bash
cat << 'MAKEFILE_EOF' > Makefile
# ============================================================
# P7: LlamaIndex 知识库应用 — Makefile
# 平台：macOS / Apple Silicon / Conda (cxllm)
# ============================================================

SHELL := /bin/bash
CONDA_BASE := $(shell conda info --base)
CONDA_ACTIVATE := source $(CONDA_BASE)/etc/profile.d/conda.sh && conda activate cxllm

export HF_ENDPOINT := https://hf-mirror.com

.PHONY: help setup download build query summary router test clean clean-all run-all

# ---- 默认目标 ----
help:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo " P7 LlamaIndex 知识库应用 — 命令列表"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@echo "  开发流程:"
	@echo "    make setup      — 一键初始化环境 + 安装依赖"
	@echo "    make download   — 下载 Embedding 模型 (BGE-Small-ZH)"
	@echo "    make build      — 构建 VectorStoreIndex 索引"
	@echo "    make query      — 启动交互式向量检索查询"
	@echo "    make summary    — 启动 SummaryIndex 全文总结查询"
	@echo "    make router     — 启动 RouterQueryEngine 多知识库路由"
	@echo "    make run-all    — 后台启动全部服务 (nohup)"
	@echo ""
	@echo "  测试 & 质量:"
	@echo "    make test       — 运行全部单元测试"
	@echo "    make test-verbose — 详细测试输出"
	@echo "    make lint       — 代码质量检查 (需要 ruff)"
	@echo ""
	@echo "  运维:"
	@echo "    make clean      — 清理缓存和构建产物"
	@echo "    make clean-all  — 深度清理 (包括模型文件)"
	@echo "    make status     — 查看运行状态 (进程 + 内存)"
	@echo "    make kill       — 停止所有后台 Python 进程"
	@echo "    make logs       — 实时查看应用日志"
	@echo ""

# ---- 环境初始化 ----
setup:
	@echo "🔧 初始化环境..."
	@$(CONDA_ACTIVATE) && \
		python --version && \
		pip install -U pip setuptools wheel -q && \
		pip install -r requirements.txt && \
		python -c "import torch; print('✅ MPS:', torch.backends.mps.is_available())"
	@echo "✅ 环境初始化完成"

# ---- 模型下载 ----
download:
	@echo "📥 下载 Embedding 模型..."
	@export HF_ENDPOINT=https://hf-mirror.com && \
		mkdir -p models && \
		hf download \
			BAAI/bge-small-zh-v1.5 \
			--local-dir models/bge-small-zh-v1.5
	@echo "✅ 模型下载完成"

# ---- 索引构建 ----
build:
	@echo "🔨 构建 VectorStoreIndex..."
	@$(CONDA_ACTIVATE) && python src/indexes/build_vector_index.py

build-summary:
	@echo "🔨 构建 SummaryIndex..."
	@$(CONDA_ACTIVATE) && python src/indexes/build_summary_index.py

# ---- 查询引擎 ----
query:
	@echo "🔍 启动 VectorStoreIndex 交互式查询..."
	@$(CONDA_ACTIVATE) && python src/query_engines/vector_query.py

summary:
	@echo "📝 启动 SummaryIndex 全文总结查询..."
	@$(CONDA_ACTIVATE) && python src/query_engines/summary_query.py

router:
	@echo "🧭 启动 RouterQueryEngine 多知识库路由..."
	@$(CONDA_ACTIVATE) && python src/routers/multi_kb_router.py

# ---- 一键启动全部服务（tmux 模式） ----
run-all-tmux:
	@echo "🚀 使用 tmux 启动全部服务..."
	@tmux new-session -d -s llamaindex -n build \
		"cd $(PWD) && $(CONDA_ACTIVATE) && echo '=== 构建索引 ===' && python src/indexes/build_vector_index.py; exec bash"
	@tmux new-window -t llamaindex -n query \
		"cd $(PWD) && $(CONDA_ACTIVATE) && sleep 3 && echo '=== 查询引擎 ===' && python src/query_engines/vector_query.py; exec bash"
	@tmux new-window -t llamaindex -n router \
		"cd $(PWD) && $(CONDA_ACTIVATE) && sleep 5 && echo '=== 路由器 ===' && python src/routers/multi_kb_router.py; exec bash"
	@tmux new-window -t llamaindex -n monitor \
		"cd $(PWD) && watch -n 3 'echo \"=== Memory ===\" && vm_stat | head -10 && echo && echo \"=== Python Processes ===\" && ps aux | grep python | grep -v grep || echo \"(none)\"'; exec bash"
	@echo ""
	@echo "✅ tmux 会话 'llamaindex' 已创建"
	@echo ""
	@echo "  连接：tmux attach -t llamaindex"
	@echo "  分屏：Ctrl+b % (垂直) / Ctrl+b \" (水平)"
	@echo "  切换：Ctrl+b o"
	@echo "  退出：Ctrl+b d (detach)"
	@echo "  终止：tmux kill-session -t llamaindex"

# ---- 一键启动全部服务（nohup 后台模式） ----
run-all:
	@echo "🚀 后台启动全部服务..."
	@mkdir -p logs
	@$(CONDA_ACTIVATE) && \
		nohup python src/indexes/build_vector_index.py \
			> logs/build.log 2>&1 & \
		echo "  build     PID $$! → logs/build.log"
	@sleep 10
	@$(CONDA_ACTIVATE) && \
		nohup python src/query_engines/vector_query.py \
			> logs/query.log 2>&1 & \
		echo "  query     PID $$! → logs/query.log"
	@echo ""
	@echo "✅ 服务已在后台启动"
	@echo "  查看日志: make logs"
	@echo "  查看状态: make status"
	@echo "  停止服务: make kill"

# ---- 测试 ----
test:
	@echo "🧪 运行单元测试..."
	@$(CONDA_ACTIVATE) && python -m pytest tests/ -v --tb=short

test-verbose:
	@echo "🧪 运行单元测试（详细模式）..."
	@$(CONDA_ACTIVATE) && python -m pytest tests/ -vv --tb=long

# ---- 代码质量 ----
lint:
	@echo "🔍 代码质量检查..."
	@$(CONDA_ACTIVATE) && ruff check src/ tests/ --fix || true
	@$(CONDA_ACTIVATE) && ruff format src/ tests/ --check || true

# ---- 运维命令 ----
status:
	@echo "📊 系统状态"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@echo "Python 进程:"
	@ps aux | grep python | grep -v grep || echo "  (无)"
	@echo ""
	@echo "统一内存:"
	@vm_stat | head -12
	@echo ""
	@echo "端口占用:"
	@lsof -i -P -n | grep python | head -10 || echo "  (无)"

logs:
	@echo "📋 实时日志 (Ctrl+C 退出)..."
	@tail -f logs/*.log 2>/dev/null || echo "  暂无日志文件，请先执行 make run-all"

kill:
	@echo "🛑 停止所有后台 Python 进程..."
	@pkill -f "src/indexes/" || true
	@pkill -f "src/query_engines/" || true
	@pkill -f "src/routers/" || true
	@sleep 1
	@echo "✅ 已停止"

# ---- 清理 ----
clean:
	@echo "🧹 清理缓存和构建产物..."
	@rm -rf storage/
	@rm -rf data/vector_store/*
	@rm -rf data/processed/*
	@rm -rf logs/*.log
	@rm -rf .pytest_cache/
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ 清理完成（模型文件已保留）"

clean-all: clean
	@echo "🧹 深度清理（包括模型文件）..."
	@rm -rf models/
	@echo "✅ 深度清理完成，下次需重新执行 make download"
EOF
```

## 5.2 tmux 多窗口管理演示

```bash
# === 一键创建 tmux 会话 ===
make run-all-tmux

# === 手动创建 tmux 会话 ===
tmux new -s llamaindex

# 分屏操作（在 tmux 内部）：
#   Ctrl+b %       → 垂直分屏
#   Ctrl+b "       → 水平分屏
#   Ctrl+b o       → 切换到下一个 pane
#   Ctrl+b 方向键  → 按方向切换 pane
#   Ctrl+b d       → detach（离开 tmux，服务继续运行）

# === 重新连接已有会话 ===
tmux attach -t llamaindex

# === 列出所有会话 ===
tmux ls

# === 彻底销毁会话 ===
tmux kill-session -t llamaindex
```

## 5.3 优雅终止（Kill）流程

```bash
# 方法 1：通过 Makefile 一键停止
make kill

# 方法 2：手动按进程名终止
pkill -f "src/query_engines/"
pkill -f "src/routers/"
pkill -f "src/indexes/"

# 方法 3：按 PID 精准终止
ps aux | grep -E "(vector_query|summary_query|multi_kb_router)" | grep -v grep
# 记下 PID，然后：
kill -15 <PID>  # SIGTERM，允许进程优雅退出
# 如果进程无响应，再使用：
kill -9 <PID>   # SIGKILL，强制终止

# 方法 4：终止 tmux 会话
tmux kill-session -t llamaindex

# 验证已全部停止
ps aux | grep python | grep -v grep
# 预期：无输出
```

## 5.4 README.md 项目说明

```bash
cat << 'EOF' > README.md
# P7: LlamaIndex 知识库应用

> 基于 LlamaIndex 构建的企业级 RAG 知识库系统，支持语义检索、全文总结、多知识库自动路由。

## 快速开始

```bash
# 1. 克隆项目
git clone <repo-url> && cd 07_llamaindex-knowledge-base-lab

# 2. 初始化环境
conda activate cxllm
make setup

# 3. 下载模型
make download

# 4. 放入文档到 data/raw/，然后构建索引
make build

# 5. 启动交互式查询
make query
```

## 核心特性

| 特性 | 说明 |
| :--- | :--- |
| VectorStoreIndex | 语义向量检索 + ChromaDB 持久化 |
| SummaryIndex | 全文树状聚合总结 |
| RouterQueryEngine | LLM 驱动的多知识库自动路由 |
| IngestionPipeline | 分块 → 元数据抽取 → 嵌入 |
| MPS 加速 | Apple Silicon Metal Performance Shaders |
| HF 镜像 | 国内 hf-mirror.com 免代理下载 |

## 目录结构

```
07_llamaindex-knowledge-base-lab/
├── configs/         # YAML 配置
├── data/
│   ├── raw/         # 原始文档（放入你的 .md/.txt/.pdf）
│   ├── processed/   # 清洗后数据
│   └── vector_store/# ChromaDB 向量库
├── src/
│   ├── loaders/     # 文档加载器
│   ├── ingestion/   # 摄取管道
│   ├── indexes/     # 索引构建
│   ├── query_engines/# 查询引擎
│   └── routers/     # 多知识库路由
├── scripts/         # Shell 脚本
├── tests/           # 单元测试
├── Makefile         # 自动化工具
└── runbook.md       # 完整操作手册
```

## 常用命令

```bash
make setup          # 安装依赖
make download       # 下载模型
make build          # 构建索引
make query          # 向量检索查询
make summary        # 全文总结查询
make router         # 多知识库路由
make run-all        # 后台启动全部服务
make test           # 运行测试
make clean          # 清理缓存
make status         # 查看运行状态
make kill           # 停止所有服务
```

## 技术栈

- **RAG 框架**: LlamaIndex 0.12+
- **向量数据库**: ChromaDB
- **Embedding**: BAAI/bge-small-zh-v1.5（中文优化）
- **LLM**: GPT-4o-mini（通过 OpenAI API）
- **加速**: Apple Silicon MPS (Metal Performance Shaders)
- **环境**: Conda + Python 3.11

## 硬件要求

- MacBook Air/Pro with Apple Silicon (M1+)
- 16GB+ 统一内存（推荐 32GB）
- 5GB+ 可用磁盘空间

## License

MIT
EOF
```

---

# 6. 常见坑点与硬件降维打击方案

## 6.1 坑点一：Embedding 维度不匹配

**现象**：

```
ValueError: shapes (1, 768) and (512, ...) not aligned
```

或查询返回乱码/空结果。

**根因**：更换了 Embedding 模型（例如从 `bge-large-zh` 的 1024 维换成 `bge-small-zh` 的 512 维），但旧索引中的向量维度仍然是旧的。

**解决**：

```bash
# 彻底清除旧索引和向量数据
rm -rf storage/
rm -rf data/vector_store/
rm -rf data/processed/

# 重建索引
make build
```

**预防**：在 `configs/model_config.yaml` 中明确记录每次使用的模型名和维度，切换模型时同步更新。

---

## 6.2 坑点二：MPS 内存溢出（OOM）

**现象**：

```
RuntimeError: MPS backend out of memory
```

尤其在批量处理大量文档时出现。

**根因**：Apple Silicon 的统一内存在 MPS 后端中没有传统的显存/主存界限，PyTorch 默认会将高水位线设得较保守。

**解决**：

```bash
# 方法 1：降低 MPS 高水位线比例（设为 0 表示无限制，由系统管理）
export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0

# 方法 2：启用高精度矩阵乘法优化（减少中间张量分配）
python -c "import torch; torch.set_float32_matmul_precision('high')"

# 方法 3：减少嵌入批次大小
# 编辑 configs/settings.yaml：
#   index.embed_batch_size: 32 → 8
```

**M5 特有优化**：M5 的内存带宽（约 120 GB/s）显著优于 M1-M3，但批量嵌入时仍需注意 Python 进程本身的内存占用。建议在 `src/utils/device.py` 的 `get_memory_info()` 中加入内存压力检测，压力达到 critical 时自动降级 batch_size。

---

## 6.3 坑点三：ChromaDB SQLite 锁冲突

**现象**：

```
sqlite3.OperationalError: database is locked
```

**根因**：多个 Python 进程同时写入同一个 ChromaDB 持久化目录。ChromaDB 底层使用 SQLite，不支持多写者并发。

**解决**：

```bash
# 1. 确保构建索引时只有单进程
# 2. 查询时可多进程读取
# 3. 如果锁卡死，手动清理 SQLite 锁文件
rm -f data/vector_store/chroma.sqlite3-lock
rm -f data/vector_store/chroma.sqlite3-wal
rm -f data/vector_store/chroma.sqlite3-shm
```

**架构原则**：构建（Write）单进程，查询（Read）可多进程。这在 Makefile 中已经体现——`make run-all` 先串行 build，再后台启动 query。

---

## 6.4 坑点四：网络代理劫持导致 HF 下载失败

**现象**：

```
ConnectionError: Failed to resolve 'huggingface.co'
HTTPSConnectionPool: Max retries exceeded
```

即使设置了 `HF_ENDPOINT=https://hf-mirror.com` 仍然失败。

**解决**：

```bash
# 1. 确认代理环境变量是否被清空（镜像下载不需要代理）
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY

# 2. 确认 HF_ENDPOINT 已正确设置
echo $HF_ENDPOINT
# 应输出：https://hf-mirror.com

# 3. 测试镜像连通性
curl -I https://hf-mirror.com 2>&1 | head -5

# 4. 如果以上都正常但仍然下载失败，换用 hfd 工具
wget https://hf-mirror.com/hfd/hfd.sh
chmod a+x hfd.sh
./hfd.sh BAAI/bge-small-zh-v1.5 --local-dir models/bge-small-zh-v1.5
```

---

## 6.5 坑点五：Windows → macOS 迁移常见痛点

| 痛点 | Windows 习惯 | macOS 正确做法 |
| :--- | :--- | :--- |
| 路径分隔符 | `data\raw\docs` | `data/raw/docs`（`Path` 对象自动处理） |
| 环境变量持久化 | `setx` 或系统设置 | `echo 'export KEY=val' >> ~/.zshrc` |
| 端口占用查看 | `netstat -ano` | `lsof -i :8000` |
| 进程终止 | `taskkill /F /PID xxx` | `kill -15 PID`（优雅）或 `kill -9 PID`（强制） |
| Conda 激活方式 | `conda activate` 直接可用 | `source $(conda info --base)/etc/profile.d/conda.sh` |
| 文件权限 | 默认无执行权限概念 | `.sh` 文件需 `chmod +x` |
| 大小写敏感 | 不敏感 | 敏感！`Data` ≠ `data` |
| 换行符 | CRLF (`\r\n`) | LF (`\n`)，通过 `.gitattributes` 强制统一 |

**防呆措施**：在 `.gitattributes` 中强制 LF：

```bash
cat << 'EOF' > .gitattributes
* text=auto eol=lf
*.py text eol=lf
*.sh text eol=lf
*.yaml text eol=lf
*.md text eol=lf
EOF
```

---

# 7. 面试深度解析

## 7.1 面试题一：LlamaIndex 的 Node 抽象比 LangChain 的 Document/Chunk 抽象好在哪里？从向量检索和知识图谱两个维度论述。

**答题思路**：

**1. 数据结构维度对比**

LangChain 的 Document → Chunk 是一条**单向降级链**：Document 被切成 Chunk 后，Chunk 之间没有结构关系，原 Document 的层级信息丢失。

LlamaIndex 的 Document → Node 是一条**保留拓扑的转换链**：Node 不仅包含文本和 Embedding，还保留了：
- `parent_node` / `child_nodes` 关系（层级保留）
- `prev_node` / `next_node` 关系（顺序保留）
- 任意自定义 `relationships`（图谱化潜力）

这意味着在检索时，一条 Node 可以**自动带回它前后的上下文**，而不需要像 LangChain 那样手动实现 "contextual retrieval"。

**2. 向量检索维度**

在向量检索场景中，LlamaIndex 的 `NodeWithScore` 携带了完整的 metadata 和 relationship 信息。当检索到 top-5 节点后，可以通过 `parent_node` 上溯找到原始 Document 的标题、作者、来源文件等结构化信息，实现**检索结果的语义归因**。

LangChain 的方案需要在 Chunk metadata 中手动复制这些信息，容易导致数据冗余和不一致。

**3. 知识图谱维度**

LlamaIndex 的 Node 原生支持 `KnowledgeGraphIndex`：将 Node.relationships 直接映射为图数据库中的边。这使得同一个 Node 可以同时存在于向量索引和知识图谱索引中，实现**混合检索（Hybrid Search）**——先用向量检索粗筛，再用图谱关系精排。

LangChain 要实现同样的效果，需要借助 GraphDB Chain 等额外组件，数据需要在多个系统间重复建模。

**4. 底层硬件视角**

在 Apple Silicon 统一内存架构上，Node 的多索引共享意味着同一份 Embedding 向量不需要在向量库和图数据库之间拷贝——所有索引共享同一块物理内存，避免了传统 x86 架构上 GPU→CPU 的数据搬运开销。这在 M5 的统一内存带宽（~120 GB/s）下尤其高效。

---

## 7.2 面试题二：解释 VectorStoreIndex 和 SummaryIndex 的底层数据流差异。从计算复杂度、内存访问模式和适用场景三个角度对比。

**答题思路**：

**1. 数据流对比**

```
VectorStoreIndex 数据流（检索阶段）：
  Query → Embedding(Query) → ANN Search → TopK Chunks → LLM 合成

SummaryIndex 数据流（检索阶段）：
  Query → 遍历全部节点 → 逐级 Tree Summarize → LLM 合成
```

**2. 计算复杂度分析**

| 维度 | VectorStoreIndex | SummaryIndex |
| :--- | :--- | :--- |
| 构建阶段 | O(N·D·E) 嵌入 N 个 chunk | O(N) 仅建树结构 |
| 检索阶段 | O(log N) ANN 搜索 | O(N) 遍历全部节点 |
| LLM 调用次数 | 1 次（合成 TopK） | O(log N) 次（逐级聚合） |
| 延迟特征 | 固定延迟（~100ms ANN + LLM） | 随文档量线性增长 |

其中：
- N = 节点数，D = 嵌入维度（512），E = 嵌入模型推理成本

**3. 内存访问模式（Apple Silicon 视角）**

VectorStoreIndex 的检索是**稀疏随机访问**：ANN 索引（HNSW 图）的每一跳访问不连续的内存地址，对 M5 的 LPDDR5 统一内存来说，随机访问延迟约为 100ns/次。HNSW 的 `ef_search` 参数直接决定了随机访问次数：`ef_search=100` 意味着最多 100 次随机内存访问。

SummaryIndex 的检索是**顺序批量访问**：遍历全部节点意味着连续读取大段内存，这恰好利用了 M5 的硬件预取器和 LPDDR5 的高带宽（~120 GB/s）。当文档量足够大时（>10,000 节点），顺序访问的优势会抵消 N 倍的计算量劣势。

**4. 适用场景决策树**

```
问题是全局性问题吗？
├── 是（"总结全文"、"主要观点有哪些"）→ SummaryIndex
└── 否（"什么是 X？"、"X 的配置是什么"）→ VectorStoreIndex
```

---

## 7.3 面试题三：在企业级 RAG 系统中，为什么 RouterQueryEngine 是必需的？从向量库膨胀、Embedding 成本和检索延迟三个工程维度论证。

**答题思路**：

**1. 向量库膨胀问题**

假设一个中型企业有 5 个独立的知识域（产品文档、代码库、运维手册、HR 政策、合规文件），每个域有 10,000 个文档片段。

- **全局单库方案**：1 个向量库包含 50,000 个向量。HNSW 索引的搜索复杂度是 O(log N)，log(50000) ≈ 10.8。而且不同域之间的语义混淆会降低检索精度——"如何配置 Kubernetes？"可能检索到 HR 政策中关于 "配置" 的无关段落。

- **Router 分库方案**：5 个各 10,000 向量的库。Router 先以 1 次轻量 LLM 调用（~100ms, ~100 tokens）确定目标库，再在目标库中进行 O(log 10000) ≈ 9.2 的搜索。

**2. Embedding 成本精算**

全局方案下，每次文档更新需要部分重建全局索引（或增量更新，但 HNSW 的增量更新会导致图结构退化）。

Router 方案下，只需重建受影响的子库。假设每天更新 1% 的文档：
- 全局方案：每次更新涉及 50,000 个向量的部分重建
- Router 方案：每次更新只涉及 10,000 个向量的部分重建

成本差 5 倍。

**3. 检索延迟精算**

在统一内存架构（M5）上：
- 全局方案延迟：50,000 向量的 HNSW 搜索 ≈ 2-5ms
- Router 方案延迟：LLM 路由决策 ~100ms + 10,000 向量 HNSW 搜索 ~1-2ms ≈ 101-102ms

Router 方案多了约 100ms 的路由决策开销，但换来了更高的检索精度和更低的长期维护成本。对于用户感知延迟（通常在 1-3 秒的 LLM 生成时间面前），这 100ms 可以忽略不计。

**4. 高级优化：缓存路由决策**

对于高频查询，可以在 Router 前增加一层语义缓存：

```
Query → 精确匹配缓存 → (命中) 直接跳转目标库
                    → (未命中) LLM Router 决策 → 缓存决策结果
```

这可以将高频查询的路由延迟降到 ~1ms 以下。

---

# 8. 最终 Checklist

```
□ configs/settings.yaml          — 运行时配置
□ configs/model_config.yaml      — 模型参数配置
□ src/utils/device.py            — MPS 设备检测 & 内存监控
□ src/utils/config.py            — YAML 配置加载器
□ src/loaders/document_loader.py — 多源文档加载器
□ src/ingestion/pipeline.py      — IngestionPipeline 摄取管道
□ src/indexes/build_vector_index.py    — VectorStoreIndex 构建器
□ src/indexes/build_summary_index.py   — SummaryIndex 构建器
□ src/query_engines/base.py            — 查询引擎抽象基类
□ src/query_engines/vector_query.py    — 向量检索交互式查询
□ src/query_engines/summary_query.py   — 全文总结交互式查询
□ src/routers/multi_kb_router.py       — RouterQueryEngine 多知识库路由
□ scripts/download_models.sh     — 模型下载（HF 镜像）
□ scripts/setup_env.sh           — 环境一键初始化
□ scripts/ingest.sh              — 文档摄取
□ scripts/query.sh               — 查询入口
□ tests/test_ingestion.py        — 摄取管道单元测试
□ tests/test_indexes.py          — 索引构建单元测试
□ tests/test_router.py           — 路由决策单元测试
□ Makefile                       — 完整自动化（25+ 命令）
□ README.md                      — 项目说明
□ .gitignore                     — Git 忽略规则
□ .gitattributes                 — 换行符统一（LF）
□ requirements.txt               — Python 依赖清单
```

完成本项目后，你已具备企业级 RAG 系统的两大主流框架能力：

- **LangChain / LangGraph** — 工作流编排与 Agent 状态机
- **LlamaIndex** — 知识库构建与检索增强生成

**下一阶段（P8）**：MCP 协议 + Tool Calling + Agent Runtime，开始构建真正可执行工具链的 AI Agent。
