"""
Text splitter — recursive chunking with configurable size and overlap.
"""

from __future__ import annotations

import re
from typing import Optional


class TextSplitter:
    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        separators: Optional[list[str]] = None,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]

    def split(self, documents: list[dict]) -> list[dict]:
        chunks = []
        for doc in documents:
            doc_id = doc.get("doc_id", "unknown")
            content = doc.get("content", "")
            text_chunks = self._split_text(content)
            for i, chunk_text in enumerate(text_chunks):
                chunks.append({
                    "chunk_id": f"{doc_id}_chunk_{i}",
                    "doc_id": doc_id,
                    "content": chunk_text,
                    "chunk_index": i,
                    "source": doc.get("source", ""),
                    "format": doc.get("format", "text"),
                })
        return chunks

    def _split_text(self, text: str) -> list[str]:
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        for sep in self.separators:
            if sep and sep in text:
                parts = self._split_by_separator(text, sep)
                for part in parts:
                    if len(part) > self.chunk_size:
                        chunks.extend(self._force_split(part))
                    else:
                        chunks.append(part)
                return self._merge_overlap(chunks)
        return self._force_split(text)

    def _split_by_separator(self, text: str, sep: str) -> list[str]:
        if not sep:
            return [text]
        parts = re.split(f"({re.escape(sep)})", text)
        result = []
        current = ""
        for part in parts:
            if len(current) + len(part) <= self.chunk_size:
                current += part
            else:
                if current.strip():
                    result.append(current.strip())
                current = part
        if current.strip():
            result.append(current.strip())
        return result

    def _force_split(self, text: str) -> list[str]:
        return [text[i:i + self.chunk_size] for i in range(0, len(text), self.chunk_size - self.chunk_overlap)]

    def _merge_overlap(self, chunks: list[str]) -> list[str]:
        if not chunks:
            return chunks
        merged = []
        current = chunks[0]
        for chunk in chunks[1:]:
            if len(current) + len(chunk) <= self.chunk_size:
                current += chunk
            else:
                if current.strip():
                    merged.append(current.strip())
                current = chunk
        if current.strip():
            merged.append(current.strip())
        return merged