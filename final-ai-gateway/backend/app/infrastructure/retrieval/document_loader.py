"""
Document loader — loads markdown, text, and PDF files into structured chunks.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class DocumentLoader:
    def __init__(self, base_dir: str = "./docs"):
        self.base_dir = Path(base_dir)

    async def load(self, source: str) -> list[dict]:
        path = self.base_dir / source if not source.startswith("/") else Path(source)
        if not path.exists():
            logger.warning("Document not found: %s", path)
            return []

        suffix = path.suffix.lower()
        if suffix == ".md":
            return self._load_markdown(path)
        elif suffix == ".txt":
            return self._load_text(path)
        elif suffix == ".pdf":
            return self._load_pdf(path)
        else:
            return self._load_text(path)

    def _load_markdown(self, path: Path) -> list[dict]:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        return [{
            "doc_id": path.stem,
            "content": text,
            "source": str(path),
            "format": "markdown",
            "size": len(text),
        }]

    def _load_text(self, path: Path) -> list[dict]:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        return [{
            "doc_id": path.stem,
            "content": text,
            "source": str(path),
            "format": "text",
            "size": len(text),
        }]

    def _load_pdf(self, path: Path) -> list[dict]:
        try:
            import PyPDF2
            with open(path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                text = "\n\n".join(page.extract_text() or "" for page in reader.pages)
        except ImportError:
            logger.warning("PyPDF2 not installed, trying raw read")
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        return [{
            "doc_id": path.stem,
            "content": text,
            "source": str(path),
            "format": "pdf",
            "size": len(text),
        }]