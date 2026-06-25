"""
RouterQueryEngine 多知识库自动路由
==================================

使用 LLMSingleSelector 自动选择最合适的知识库回答用户问题。

数据流：
  用户问题 → LLMSingleSelector
    ├── 适合 tech_notes → 路由到 notes 知识库
    └── 适合 academic_papers → 路由到 papers 知识库
    → VectorStoreIndex.as_query_engine() → 生成答案

两个知识库：
  - tech_notes: 学习笔记（Transformer/Attention/KV Cache/RoPE/MoE/LoRA/RLHF）
  - academic_papers: 学术论文（Attention is All You Need/LoRA/DPO）

路由原理：LLMSingleSelector 根据 ToolMetadata.description 匹配查询意图，
会选择语义最接近的知识库。verbose=True 可查看路由决策过程。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from llama_index.core import Settings, VectorStoreIndex
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core.query_engine import RouterQueryEngine
from llama_index.core.selectors import LLMSingleSelector
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.ollama import Ollama
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
        config: 全局配置对象
        data_subdir: data/raw/ 下的子目录名
        name: 知识库唯一标识名
        description: 知识库描述（LLMSingleSelector 据此做路由决策）

    Returns:
        可被 RouterQueryEngine 使用的 QueryEngineTool
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
    console.print("[bold magenta]  RouterQueryEngine 多知识库路由 (本地 Qwen2.5)[/bold magenta]")
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

    router = RouterQueryEngine(
        selector=LLMSingleSelector.from_defaults(),
        query_engine_tools=[tool_notes, tool_papers],
        verbose=True,
    )

    table = Table(title="🗺️ 路由表")
    table.add_column("知识库", style="cyan")
    table.add_column("名称", style="green")
    table.add_column("适用场景", style="dim")
    table.add_row("tech_notes", "技术笔记", "基础概念、技术原理")
    table.add_row("academic_papers", "学术论文", "论文方法、数学推导")
    console.print(table)

    console.print("\n[bold green]💬 输入问题测试自动路由，输入 'exit' 退出[/bold green]")
    console.print("[dim]   Router 会自动选择最合适的知识库来回答[/dim]")
    console.print("[dim]   全本地运行，无需 API Key[/dim]\n")

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

        tool_name = response.metadata.get("tool_name", "unknown") if response.metadata else "unknown"

        console.print(Panel(
            str(response),
            title=f"🤖 回答 [路由: {tool_name}]",
            border_style="green" if tool_name != "unknown" else "red",
        ))
        console.print()


if __name__ == "__main__":
    main()
