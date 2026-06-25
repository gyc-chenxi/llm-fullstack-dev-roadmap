"""
SummaryIndex 查询引擎
========================

summary_index.as_query_engine(response_mode="tree_summarize")
以 Tree Summarize 模式逐级聚合全部文档内容。

与 VectorStoreIndex 查询的区别：
  - VectorStoreIndex: 仅检索 top-K 相关片段（高效但可能遗漏全局信息）
  - SummaryIndex: 遍历所有 Node（全局覆盖但速度慢，随文档量线性增长）
  - 适合"总结全文"、"概括所有文档"的宏观问题

Tree Summarize 策略：
  1. 将所有 Node 分组（每组 ~5 个）
  2. LLM 对每组进行局部总结
  3. 将所有局部总结再次分组总结
  4. 重复直到只剩一个总结 → 最终答案

全本地运行：BGE-Small-ZH + Ollama Qwen2.5:7b
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from llama_index.core import Settings, SummaryIndex
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from src.utils.config import Config
from src.utils.device import detect_device
from src.loaders.document_loader import load_local_documents

console = Console()


def main():
    console.print("[bold magenta]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold magenta]")
    console.print("[bold magenta]  SummaryIndex 全文总结查询 (本地 Qwen2.5)[/bold magenta]")
    console.print("[bold magenta]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold magenta]")

    config = Config.load("configs/settings.yaml")
    device = detect_device()

    Settings.embed_model = HuggingFaceEmbedding(
        model_name=config.get("embedding.model_name", "models/bge-small-zh-v1.5"),
        device=device,
    )
    Settings.llm = Ollama(
        model=config.get("llm.model", "qwen2.5:7b"),
        temperature=0.0,
        request_timeout=120.0,
    )

    documents = load_local_documents(input_dir=config.get("data.raw_dir", "data/raw"))
    summary_index = SummaryIndex.from_documents(documents)

    query_engine = summary_index.as_query_engine(
        response_mode="tree_summarize",
        streaming=True,
    )

    console.print("[bold green]💬 输入问题（建议：总结/概括/全文性问题），输入 'exit' 退出[/bold green]")
    console.print("[dim]   全本地运行，无需 API Key[/dim]\n")

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
