"""
VectorStoreIndex 查询引擎
============================

从 ChromaDB 持久化存储加载 VectorStoreIndex，运行本地 LLM 进行 RAG 问答。

数据流：
  用户问题 → VectorStoreIndex.as_query_engine(similarity_top_k=5)
    → BGE Embedding(问题) → ChromaDB 向量检索 → top-5 相关 Node
    → Ollama Qwen2.5:7B (compact 模式) → 生成答案 + 引用来源
    → rich Panel 美化输出

全本地运行（无需任何 API Key）：
  - Embedding: BAAI/bge-small-zh-v1.5 (本地模型, 512维)
  - LLM: Ollama qwen2.5:7b (本地推理)
  - Vector Store: ChromaDB PersistentClient (本地文件)

response_mode="compact": 将检索片段压缩成单个 prompt，减少 LLM 调用次数。
streaming=True: 启用流式输出（token 级逐字返回）。
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
from llama_index.llms.ollama import Ollama
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

    数据流：ChromaDB → ChromaVectorStore → StorageContext → load_index_from_storage
    """
    chroma_client = chromadb.PersistentClient(
        path=config.get("vector_store.persist_dir", "data/vector_store")
    )
    collection_name = config.get("vector_store.collection_name", "llamaindex_kb")

    try:
        chroma_collection = chroma_client.get_collection(collection_name)
    except Exception as e:
        console.print(
            f"[red]❌ ChromaDB Collection '{collection_name}' 不存在！[/red]\n"
            f"[yellow]   请先构建索引: make build[/yellow]"
        )
        raise SystemExit(1)

    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(
        persist_dir=config.get("index.persist_dir", "storage"),
        vector_store=vector_store,
    )

    index = load_index_from_storage(storage_context)
    console.print(f"[green]✅ 索引加载成功[/green]")
    return index


def main():
    """交互式查询 REPL — 全本地模型（无 API Key 依赖）。"""
    console.print("[bold magenta]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold magenta]")
    console.print("[bold magenta]  VectorStoreIndex 查询引擎 (本地 Qwen2.5)[/bold magenta]")
    console.print("[bold magenta]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold magenta]")

    config = Config.load("configs/settings.yaml")
    device = detect_device()

    # Embedding：本地 BGE 模型
    Settings.embed_model = HuggingFaceEmbedding(
        model_name=config.get("embedding.model_name", "models/bge-small-zh-v1.5"),
        device=device,
    )
    console.print(f"[blue]🔌 Embedding: {config.get('embedding.model_name')} on {device}[/blue]")

    # LLM：本地 Ollama Qwen2.5
    Settings.llm = Ollama(
        model=config.get("llm.model", "qwen2.5:7b"),
        temperature=config.get("llm.temperature", 0.0),
        request_timeout=120.0,
    )
    console.print(f"[blue]🧠 LLM: {config.get('llm.model', 'qwen2.5:7b')} (Ollama 本地)[/blue]")

    index = load_index(config)

    query_engine = index.as_query_engine(
        similarity_top_k=config.get("index.similarity_top_k", 5),
        streaming=True,
        response_mode="compact",
    )

    console.print("[bold green]💬 输入问题开始查询，输入 'exit' 退出[/bold green]")
    console.print("[dim]   全本地运行，无需 API Key[/dim]\n")

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

        console.print("[dim]⏳ 检索 + 生成中...[/dim]")
        response = query_engine.query(question)

        console.print(Panel(
            Markdown(str(response)),
            title="🤖 回答 (Qwen2.5 本地)",
            border_style="green",
        ))

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
