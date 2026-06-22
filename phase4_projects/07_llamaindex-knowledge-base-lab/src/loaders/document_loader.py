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
