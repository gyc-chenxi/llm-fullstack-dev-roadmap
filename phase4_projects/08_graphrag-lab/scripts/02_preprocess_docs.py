#!/usr/bin/env python3
"""Document preprocessing for GraphRAG ingestion.

Reads raw .txt files from data/raw/, applies:
- Null-byte striping
- CRLF → LF normalization
- Excessive blank line collapsing
- Trailing whitespace cleanup
- Minimum character filter

Writes cleaned .txt to data/input/ for GraphRAG indexing.

Usage:
    PYTHONPATH=. python scripts/02_preprocess_docs.py --input data/raw --output data/input
"""

import os
import re
import sys
import argparse
from pathlib import Path


def clean_text(text: str) -> str:
    """Normalize text for GraphRAG ingestion."""
    # Strip null bytes
    text = text.replace("\x00", "")
    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Collapse 3+ blank lines into 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Per-line: strip trailing spaces, preserve paragraph breaks
    lines = []
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped:
            lines.append(stripped)
        elif lines and lines[-1] != "":
            lines.append("")
    # Drop trailing empty lines
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def estimate_tokens(text: str) -> int:
    """Estimate token count using cl100k_base (matches GraphRAG default)."""
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except ImportError:
        # Fallback: rough heuristic (~1.3 tokens per word for English)
        return int(len(text.split()) * 1.3)


def main():
    parser = argparse.ArgumentParser(
        description="Preprocess documents for GraphRAG ingestion"
    )
    parser.add_argument("--input", default="data/raw",
                        help="Directory with raw .txt files")
    parser.add_argument("--output", default="data/input",
                        help="Directory for cleaned .txt files")
    parser.add_argument("--min-chars", type=int, default=200,
                        help="Minimum character count to keep a document")
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)

    if not input_dir.exists():
        print(f"[preprocess] ERROR: input directory not found: {input_dir}")
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    # Clear previous output
    for f in output_dir.glob("*.txt"):
        f.unlink()
        print(f"[preprocess] removed stale: {f.name}")

    # Gather input files
    files = sorted(
        list(input_dir.glob("*.txt")) +
        list(input_dir.glob("*.md"))
    )
    if not files:
        print(f"[preprocess] ERROR: no .txt or .md files found in {input_dir}")
        print("[preprocess] Run download-corpus first: bash scripts/01_download_corpus.sh")
        sys.exit(1)

    print(f"[preprocess] Processing {len(files)} raw files...")
    print(f"[preprocess] Min chars: {args.min_chars}, Output: {output_dir}/")
    print()

    total_tokens = 0
    written = 0
    skipped = 0

    for i, fp in enumerate(files):
        try:
            raw = fp.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            print(f"  [{i+1:3d}/{len(files)}] SKIP {fp.name}: read error — {e}")
            skipped += 1
            continue

        cleaned = clean_text(raw)
        if len(cleaned) < args.min_chars:
            print(f"  [{i+1:3d}/{len(files)}] SKIP {fp.name}: too short ({len(cleaned)} chars < {args.min_chars})")
            skipped += 1
            continue

        out_name = fp.stem[:100] + ".txt"
        out_path = output_dir / out_name
        out_path.write_text(cleaned, encoding="utf-8")

        tokens = estimate_tokens(cleaned)
        total_tokens += tokens
        print(f"  [{i+1:3d}/{len(files)}] OK   {out_name:50s} {len(cleaned):>6,} chars  ~{tokens:>6,} tokens")
        written += 1

    print()
    print("=" * 60)
    print(f"[preprocess] SUMMARY:")
    print(f"  Raw files scanned : {len(files)}")
    print(f"  Cleaned & written : {written}")
    print(f"  Skipped           : {skipped}")
    print(f"  Total tokens (est): ~{total_tokens:,}")
    print(f"  Output directory  : {output_dir}/")
    print("=" * 60)


if __name__ == "__main__":
    main()
