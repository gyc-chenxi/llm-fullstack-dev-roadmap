from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup
from markdown_it import MarkdownIt
from pypdf import PdfReader


SUPPORTED_SUFFIXES = {".pdf", ".txt", ".md", ".markdown", ".html", ".htm"}


def load_documents(input_dir: str | Path) -> list[dict]:
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
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return load_pdf(path)

    if suffix in {".md", ".markdown"}:
        return load_markdown(path)

    if suffix in {".html", ".htm"}:
        return load_html(path)

    return path.read_text(encoding="utf-8", errors="ignore")


def load_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    pages: list[str] = []

    for page_idx, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if text.strip():
            pages.append(f"\n\n[page {page_idx + 1}]\n{text}")

    return "\n".join(pages)


def load_markdown(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    # 这里不转 HTML，只做一次 markdown 解析验证，防止坏文件。
    MarkdownIt().parse(raw)
    return raw


def load_html(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(raw, "html.parser")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    return soup.get_text("\n")