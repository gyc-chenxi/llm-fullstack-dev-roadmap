"""
VectorStoreIndex 构建器
=========================

构建 LlamaIndex VectorStoreIndex + ChromaDB 持久化向量存储。

数据流：
  configs/settings.yaml → Config.load()
    ↓
  data/raw/*.{md,txt,pdf} → load_local_documents() → List[Document]
    ↓
  document → IngestionPipeline(分块+嵌入) → Nodes (含 BGE 512维向量)
    ↓
  Nodes → ChromaVectorStore → ChromaDB PersistentClient
    ↓
  VectorStoreIndex.from_documents(docs, storage_context, embed_batch_size=32)
    ↓
  index.storage_context.persist() → storage/（LlamaIndex 元数据）
  ChromaDB 数据 → data/vector_store/（向量存储）

两层存储：
  - storage/: LlamaIndex 索引元数据（docstore.json, index_store.json 等）
  - data/vector_store/: ChromaDB 原始向量 + 文档（chroma.sqlite3）

用法：PYTHONPATH=src python src/indexes/build_vector_index.py
"""

import sys
from pathlib import Path

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

    print_device_info()

    config = Config.load("configs/settings.yaml")
    device = detect_device()

    # Embedding 模型：BGE-Small-ZH（本地，无需联网）
    Settings.embed_model = HuggingFaceEmbedding(
        model_name=config.get("embedding.model_name", "BAAI/bge-small-zh-v1.5"),
        device=device,
        max_length=config.get("embedding.max_length", 512),
    )
    console.print(f"[blue]🔌 Embedding 模型: {config.get('embedding.model_name')} on {device}[/blue]")

    documents = load_local_documents(input_dir=config.get("data.raw_dir", "data/raw"))
    if not documents:
        console.print("[red]❌ 未找到文档！请将 .md/.txt/.pdf 放入 data/raw/ 目录[/red]")
        sys.exit(1)

    stats = get_document_stats(documents)
    console.print(f"[blue]📊 文档统计: {stats['total_docs']} 个, {stats['total_chars']:,} 字符[/blue]")

    # ChromaDB 持久化客户端
    ensure_dir(config.get("vector_store.persist_dir", "data/vector_store"))
    chroma_client = chromadb.PersistentClient(
        path=config.get("vector_store.persist_dir", "data/vector_store")
    )

    collection_name = config.get("vector_store.collection_name", "llamaindex_kb")
    try:
        chroma_collection = chroma_client.get_collection(collection_name)
        console.print(f"[yellow]⚠️  复用已存在的 ChromaDB Collection: {collection_name}[/yellow]")
    except Exception:
        chroma_collection = chroma_client.create_collection(collection_name)
        console.print(f"[green]✅ 创建 ChromaDB Collection: {collection_name}[/green]")

    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    console.print("[bold blue]🔨 构建 VectorStoreIndex（这可能需要几分钟）...[/bold blue]")
    index = VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        embed_batch_size=config.get("index.embed_batch_size", 32),
        show_progress=True,
    )

    persist_dir = config.get("index.persist_dir", "storage")
    ensure_dir(persist_dir)
    index.storage_context.persist(persist_dir=persist_dir)

    console.print(f"[green]✅ VectorStoreIndex 构建完成[/green]")
    console.print(f"[green]   LlamaIndex 索引 → {persist_dir}/[/green]")
    console.print(f"[green]   ChromaDB 向量  → {config.get('vector_store.persist_dir')}/[/green]")

    return index


if __name__ == "__main__":
    main()
