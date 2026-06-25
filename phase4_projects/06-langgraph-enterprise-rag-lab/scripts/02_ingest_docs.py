"""
文档摄入脚本
==============

完整的数据摄入管线：

数据流：
  data/raw/*.{pdf,md,txt,html} → load_documents()
    → [{source, title, text}]
    → chunk_text(text, 700, 120)
    → [{id, content, metadata}]
    → 过滤 < 30 字符
    → 保存到 data/processed/chunks.jsonl（可审计）
    → BGE-M3.encode(contents, batch=16)
    → ChromaDB.upsert(ids, documents, metadatas, embeddings)

用法：
  python scripts/02_ingest_docs.py                     # 增量入库
  python scripts/02_ingest_docs.py --reset             # 清空重建
  python scripts/02_ingest_docs.py --input data/custom --collection my_corpus
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import chromadb

from langgraph_enterprise_rag.retrieval.chunking import chunk_text
from langgraph_enterprise_rag.retrieval.embeddings import build_embedding_model
from langgraph_enterprise_rag.retrieval.loaders import load_documents
from langgraph_enterprise_rag.utils.hashing import stable_hash


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest local docs into Chroma.")
    parser.add_argument("--input", default="data/raw", help="Raw document directory.")
    parser.add_argument("--chroma-dir", default="data/chroma", help="Chroma persist dir.")
    parser.add_argument(
        "--collection",
        default="enterprise_rag_docs",
        help="Chroma collection name.",
    )
    parser.add_argument("--chunk-size", type=int, default=700)
    parser.add_argument("--chunk-overlap", type=int, default=120)
    parser.add_argument("--reset", action="store_true", help="Delete collection first.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    input_dir = Path(args.input)
    chroma_dir = Path(args.chroma_dir)
    processed_dir = Path("data/processed")

    chroma_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    docs = load_documents(input_dir)
    print(f"[ingest] loaded files: {len(docs)}")

    if not docs:
        print("[warn] no documents found. Put PDF/MD/TXT/HTML files into data/raw first.")
        return

    chunks: list[dict] = []

    for doc in docs:
        parts = chunk_text(
            doc["text"],
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
        )

        for idx, content in enumerate(parts):
            content = content.strip()
            if len(content) < 30:
                continue

            doc_id = stable_hash(doc["source"])
            chunk_id = f"{doc_id}-{idx:05d}"

            chunks.append(
                {
                    "id": chunk_id,
                    "content": content,
                    "metadata": {
                        "source": doc["source"],
                        "title": doc.get("title") or Path(doc["source"]).name,
                        "chunk_index": idx,
                        "doc_id": doc_id,
                        "content_hash": stable_hash(content),
                    },
                }
            )

    print(f"[chunking] total chunks: {len(chunks)}")

    if not chunks:
        print("[warn] no valid chunks generated.")
        return

    # 保存 chunks.jsonl 用于审计和调试
    chunk_jsonl = processed_dir / "chunks.jsonl"
    with chunk_jsonl.open("w", encoding="utf-8") as f:
        for row in chunks:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"[processed] chunks saved: {chunk_jsonl}")

    # BGE-M3 编码
    embedder = build_embedding_model()
    print(f"[embedding] model: {embedder.model_name}")

    texts = [x["content"] for x in chunks]
    embeddings = embedder.encode(texts)

    # ChromaDB 持久化
    client = chromadb.PersistentClient(path=str(chroma_dir))

    if args.reset:
        try:
            client.delete_collection(args.collection)
            print(f"[chroma] deleted old collection: {args.collection}")
        except Exception:
            pass

    collection = client.get_or_create_collection(name=args.collection)

    ids = [x["id"] for x in chunks]
    documents = [x["content"] for x in chunks]
    metadatas = [x["metadata"] for x in chunks]

    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=embeddings,
    )

    print(f"[chroma] collection: {args.collection}")
    print(f"[chroma] count: {collection.count()}")
    print(f"[chroma] persisted dir: {chroma_dir}")
    print("[done] ingest completed")


if __name__ == "__main__":
    main()
