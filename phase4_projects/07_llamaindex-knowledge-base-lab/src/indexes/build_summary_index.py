"""
SummaryIndex 构建器
=====================

构建 LlamaIndex SummaryIndex 用于全文总结类查询。

与 VectorStoreIndex 的区别：
  - VectorStoreIndex: 语义向量检索，适合精确问答
  - SummaryIndex: 全文档遍历总结，适合"概括全文内容"类查询
  - SummaryIndex 不存储向量索引，而是按 doc_id 顺序遍历所有 Node

数据流：
  Documents → SummaryIndex.from_documents(docs, show_progress=True)
    → 遍历全部 Node → Tree Summarize → 生成总结

使用场景：
  "总结知识库中有哪些关键技术"
  "概括所有文档的主要观点"

注意：SummaryIndex 不适合精确事实性查询，因为需要遍历全部文档。
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
