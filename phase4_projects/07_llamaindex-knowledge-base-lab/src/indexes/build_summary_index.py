#!/usr/bin/env python3
"""SummaryIndex 构建器：全文总结索引."""

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
