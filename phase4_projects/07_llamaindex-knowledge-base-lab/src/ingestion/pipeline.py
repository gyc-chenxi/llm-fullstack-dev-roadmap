"""
文档摄取管道
===============

基于 LlamaIndex IngestionPipeline 的文档处理管线。

数据流：
  Document → SentenceSplitter(chunk_size=500, overlap=50)
    → [可选] TitleExtractor (LLM 提取标题)
    → [可选] QuestionsAnsweredExtractor (LLM 生成 QA 对)
    → HuggingFaceEmbedding (BGE-Small-ZH, dim=512)
    → List[BaseNode] → ChromaDB VectorStore

LLM 元数据抽取的可选性：
  - 若设置了 DEEPSEEK_API_KEY 或 OPENAI_API_KEY → 启用 TitleExtractor + QuestionsAnsweredExtractor
  - 若未设置 API Key → 自动跳过 LLM 抽取，仅执行分块 + 嵌入

缓存机制：
  通过文档内容 SHA256 hash 判断是否需要重新摄取，
  缓存文件保存在 data/processed/nodes_{hash}.json。
"""

import hashlib
import json
import os
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


def _check_llm_available() -> bool:
    """检测 LLM 是否可用（支持 DEEPSEEK_API_KEY 或 OPENAI_API_KEY）。"""
    return bool(os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY"))


def build_ingestion_pipeline(
    config: Config,
    embedding_model: Optional[HuggingFaceEmbedding] = None,
) -> IngestionPipeline:
    """构建文档摄取管道。

    Pipeline 顺序（transformations 列表）：
        1. SentenceSplitter          — 按语义边界分块（必需，始终启用）
        2. TitleExtractor            — LLM 提取标题（可选，需 API Key）
        3. QuestionsAnsweredExtractor — LLM 生成 QA 对（可选，需 API Key）
        4. HuggingFaceEmbedding      — BGE 向量嵌入（必需，始终启用）

    参数选择：
      chunk_size=500: 中文约 250-350 字，BGE-small-zh 的 max_length=512 不会截断
      chunk_overlap=50: 10% 重叠，确保跨边界实体连接性
      paragraph_separator="\\n\\n": 在段落边界处优先断开
    """
    chunk_size = config.get("index.chunk_size", 500)
    chunk_overlap = config.get("index.chunk_overlap", 50)

    if embedding_model is None:
        embedding_model = HuggingFaceEmbedding(
            model_name=config.get("embedding.model_name", "BAAI/bge-small-zh-v1.5"),
            device=config.get("embedding.device", "mps"),
            max_length=config.get("embedding.max_length", 512),
        )

    llm_available = _check_llm_available()

    transformations = [
        SentenceSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            paragraph_separator="\n\n",
        ),
    ]

    if llm_available:
        transformations.append(
            TitleExtractor(
                llm=None,  # 使用全局 Settings.llm
                nodes=5,
            )
        )
        transformations.append(
            QuestionsAnsweredExtractor(
                llm=None,
                questions=3,
            )
        )
    else:
        console.print(
            "[yellow]⚠️  未检测到 DEEPSEEK_API_KEY，跳过 LLM 元数据抽取（TitleExtractor / QuestionsAnsweredExtractor）[/yellow]\n"
            "[dim]  如需启用，请设置: export DEEPSEEK_API_KEY='sk-...'[/dim]"
        )

    transformations.append(embedding_model)

    pipeline = IngestionPipeline(transformations=transformations)

    console.print(
        f"[bold blue]🔧 摄取管道配置:[/bold blue]\n"
        f"   chunk_size={chunk_size}, chunk_overlap={chunk_overlap}\n"
        f"   embedding={config.get('embedding.model_name')}\n"
        f"   llm_extractors={'enabled' if llm_available else 'disabled'}"
    )

    return pipeline


def run_ingestion(
    documents: List[Document],
    pipeline: Optional[IngestionPipeline] = None,
    config: Optional[Config] = None,
    cache_dir: str = "data/processed",
) -> List[BaseNode]:
    """执行文档摄取，生成 Nodes（含缓存检查）。

    缓存策略：通过文档内容 hash 判断是否需要重新摄取。
    若缓存命中则跳过 pipeline 执行，直接提示。

    Returns:
        生成的 BaseNode 列表（每个 Node 含 embedding、text、metadata）
    """
    if config is None:
        config = Config.load("configs/settings.yaml")

    doc_hash = _compute_docs_hash(documents)
    cache_path = Path(cache_dir) / f"nodes_{doc_hash}.json"

    if cache_path.exists():
        console.print(f"[yellow]⚠️  发现缓存: {cache_path.name}，跳过摄取[/yellow]")
        console.print("[yellow]   如需强制重建请删除 data/processed/ 目录[/yellow]")

    if pipeline is None:
        pipeline = build_ingestion_pipeline(config)

    ensure_dir(cache_dir)

    console.print(f"[bold blue]🚀 开始摄取 {len(documents)} 个文档...[/bold blue]")

    with Progress() as progress:
        task = progress.add_task("[cyan]摄取中...", total=len(documents))
        nodes = pipeline.run(documents=documents, show_progress=True)

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
    """计算文档列表的内容哈希（用于摄取缓存判断）。

    按 doc_id 排序确保确定性：相同文档集总能生成相同 hash。
    """
    hasher = hashlib.sha256()
    for doc in sorted(documents, key=lambda d: d.doc_id or ""):
        hasher.update((doc.doc_id or "").encode())
        hasher.update(doc.text[:200].encode())
    return hasher.hexdigest()[:12]
