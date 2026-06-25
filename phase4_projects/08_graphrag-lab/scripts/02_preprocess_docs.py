"""
文档预处理（GraphRAG 摄入）
=============================

将 data/raw/ 中的语料清洗后输出到 data/input/ 供 GraphRAG 索引使用。

处理步骤：
  - null-byte 剥离：\x00 去除（BERT tokenizer 无法处理）
  - CRLF→LF：统一换行符
  - 多余空行折叠：3+ 空行 → 1 空行
  - 行尾空白清理
  - 最小字符过滤（--min-chars，默认 200 字符）

Token 估算：
  - 优先使用 tiktoken cl100k_base（GraphRAG 默认 tokenizer）
  - 回退为 1.3× 词数启发式（英文）

用法：
  PYTHONPATH=. python scripts/02_preprocess_docs.py --input data/raw --output data/input
"""

import os
import re
import sys
import argparse
from pathlib import Path


def clean_text(text: str) -> str:
    """标准化文本以便 GraphRAG 摄入。"""
    text = text.replace("\x00", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)

    lines = []
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped:
            lines.append(stripped)
        elif lines and lines[-1] != "":
            lines.append("")
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def estimate_tokens(text: str) -> int:
    """使用 cl100k_base 估算 token 数（与 GraphRAG 默认编码器匹配）。"""
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except ImportError:
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

    for f in output_dir.glob("*.txt"):
        f.unlink()
        print(f"[preprocess] removed stale: {f.name}")

    files = sorted(
        list(input_dir.glob("*.txt")) +
        list(input_dir.glob("*.md"))
    )
    if not files:
        print(f"[preprocess] ERROR: no .txt or .md files found in {input_dir}")
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
