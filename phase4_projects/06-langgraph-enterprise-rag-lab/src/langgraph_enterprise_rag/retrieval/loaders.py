"""
文档加载器
============

支持 PDF、Markdown、HTML、TXT 四种格式的文档加载。

数据流：
  data/raw/*.{pdf,md,txt,html} → 递归扫描 → 按后缀分发 loader
  → extract text → [{source, title, text}] → 传入 chunking pipeline

各格式处理策略：
  - PDF: pypdf.PdfReader，按页提取并标记 [page N]
  - Markdown: markdown-it 解析验证（不做渲染，保留原文）
  - HTML: BeautifulSoup 去除 script/style/noscript 后提取纯文本
  - TXT: 直接读取 UTF-8
"""

from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup
from markdown_it import MarkdownIt
from pypdf import PdfReader


SUPPORTED_SUFFIXES = {".pdf", ".txt", ".md", ".markdown", ".html", ".htm"}


def load_documents(input_dir: str | Path) -> list[dict]:
    """递归加载目录下所有支持的文档文件。

    Returns:
        [{source: 文件路径, title: 文件名, text: 提取的纯文本}]
    """
    root = Path(input_dir)
    if not root.exists():
        return []

    docs: list[dict] = []

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue

        if path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue

        try:
            text = load_one_file(path)
            if text.strip():
                docs.append(
                    {
                        "source": str(path),
                        "title": path.name,
                        "text": text,
                    }
                )
        except Exception as exc:
            print(f"[loader][warn] failed: {path} -> {exc!r}")

    return docs


def load_one_file(path: Path) -> str:
    """按文件后缀分派到对应的 loader。"""
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return load_pdf(path)

    if suffix in {".md", ".markdown"}:
        return load_markdown(path)

    if suffix in {".html", ".htm"}:
        return load_html(path)

    return path.read_text(encoding="utf-8", errors="ignore")


def load_pdf(path: Path) -> str:
    """使用 pypdf 提取 PDF 文本，按页标记 [page N] 分隔。"""
    reader = PdfReader(str(path))
    pages: list[str] = []

    for page_idx, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if text.strip():
            pages.append(f"\n\n[page {page_idx + 1}]\n{text}")

    return "\n".join(pages)


def load_markdown(path: Path) -> str:
    """读取 Markdown 原文，使用 markdown-it 做解析验证。"""
    raw = path.read_text(encoding="utf-8", errors="ignore")
    MarkdownIt().parse(raw)
    return raw


def load_html(path: Path) -> str:
    """提取 HTML 纯文本，去除 script/style/noscript 标签。"""
    raw = path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(raw, "html.parser")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    return soup.get_text("\n")
