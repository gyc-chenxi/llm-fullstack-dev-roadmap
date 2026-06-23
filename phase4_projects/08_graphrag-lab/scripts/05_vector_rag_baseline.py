#!/usr/bin/env python3
"""Build Vector RAG baseline with Chroma + BGE-M3.

This provides a traditional dense-retrieval baseline to compare against GraphRAG.
Uses the same BGE-M3 embedding model and the same chunk size for fairness.

Pipeline:
  1. Load all .txt from data/input/
  2. Sliding-window chunk (size=1200, overlap=100 — matches GraphRAG default)
  3. Encode all chunks with BGE-M3 on MPS
  4. Persist to Chroma vector store
  5. Run a test query to verify

Usage:
    PYTHONPATH=. python scripts/05_vector_rag_baseline.py \
        --input data/input \
        --vector-store data/vector_store \
        --embedding-model BAAI/bge-m3 \
        --chunk-size 1200 \
        --chunk-overlap 100
"""

import os
import sys
import argparse
import time
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer


def chunk_text(text: str, chunk_size: int = 1200, overlap: int = 100) -> list:
    """Simple sliding-window word-level chunking.

    Matches GraphRAG's default chunk_size to ensure fair comparison.
    """
    words = text.split()
    if not words:
        return []
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap
        if start >= len(words):
            break
    return chunks


def main():
    parser = argparse.ArgumentParser(
        description="Build Vector RAG baseline (Chroma + BGE-M3)"
    )
    parser.add_argument("--input", default="data/input",
                        help="Directory with preprocessed .txt files")
    parser.add_argument("--vector-store", default="data/vector_store",
                        help="Chroma persistence directory")
    parser.add_argument("--embedding-model", default="BAAI/bge-m3",
                        help="SentenceTransformer model name")
    parser.add_argument("--chunk-size", type=int, default=1200,
                        help="Words per chunk (match GraphRAG)")
    parser.add_argument("--chunk-overlap", type=int, default=100,
                        help="Word overlap between chunks")
    parser.add_argument("--collection", default="graphrag_lab_corpus",
                        help="Chroma collection name")
    parser.add_argument("--device", default="mps",
                        help="Torch device (mps/cpu/cuda)")
    parser.add_argument("--embed-batch-size", type=int, default=16,
                        help="Batch size for encoding (lower on MPS ≤32GB)")
    args = parser.parse_args()

    # --- Load documents ---
    input_dir = Path(args.input)
    if not input_dir.exists():
        print(f"[VectorRAG] ERROR: input directory not found: {input_dir}")
        sys.exit(1)

    txt_files = sorted(input_dir.glob("*.txt"))
    if not txt_files:
        print(f"[VectorRAG] ERROR: no .txt files in {input_dir}")
        print("[VectorRAG] Run: make download-corpus && make preprocess")
        sys.exit(1)

    # --- Load embedding model ---
    print(f"[VectorRAG] Loading {args.embedding_model} on {args.device} ...")
    t0 = time.time()
    model = SentenceTransformer(args.embedding_model, device=args.device)
    print(f"[VectorRAG] Model loaded in {time.time()-t0:.1f}s, "
          f"dim={model.get_sentence_embedding_dimension()}, "
          f"max_seq_len={model.max_seq_length}")

    # --- Chunking ---
    print(f"[VectorRAG] Chunking {len(txt_files)} documents "
          f"(chunk_size={args.chunk_size}, overlap={args.chunk_overlap})...")
    all_chunks = []
    all_metadata = []
    all_ids = []

    for fp in txt_files:
        text = fp.read_text(encoding="utf-8")
        chunks = chunk_text(text, args.chunk_size, args.chunk_overlap)
        for j, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            all_metadata.append({
                "source": fp.name,
                "chunk_index": j,
                "char_length": len(chunk),
            })
            all_ids.append(f"{fp.stem}_{j}")

    print(f"[VectorRAG] Total chunks: {len(all_chunks)}")

    # --- Encode ---
    print(f"[VectorRAG] Encoding {len(all_chunks)} chunks "
          f"(batch_size={args.embed_batch_size})...")
    t0 = time.time()
    embeddings = model.encode(
        all_chunks,
        batch_size=args.embed_batch_size,
        show_progress_bar=True,
        normalize_embeddings=True,
    )
    encode_time = time.time() - t0
    print(f"[VectorRAG] Encoding done in {encode_time:.1f}s "
          f"({len(all_chunks)/encode_time:.1f} chunks/s), "
          f"shape={embeddings.shape}")

    # --- Build Chroma index ---
    print(f"[VectorRAG] Building Chroma index at {args.vector_store} ...")
    store_path = Path(args.vector_store)
    store_path.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(store_path))

    # Drop existing collection to rebuild cleanly
    try:
        client.delete_collection(args.collection)
        print(f"[VectorRAG] Deleted existing collection '{args.collection}'")
    except Exception:
        pass

    collection = client.create_collection(
        name=args.collection,
        metadata={"hnsw:space": "cosine"},
    )

    # Batch insert
    insert_batch = 500
    for i in range(0, len(all_chunks), insert_batch):
        end = min(i + insert_batch, len(all_chunks))
        collection.add(
            ids=all_ids[i:end],
            embeddings=embeddings[i:end].tolist(),
            documents=all_chunks[i:end],
            metadatas=all_metadata[i:end],
        )
        print(f"  [{end:5d}/{len(all_chunks)}] inserted")

    print(f"[VectorRAG] Persisted: {args.vector_store}/")
    print(f"[VectorRAG] Collection '{args.collection}': {collection.count()} vectors")

    # --- Quick test query ---
    test_query = "What is the Transformer architecture?"
    print(f"\n[VectorRAG] Test query: '{test_query}'")
    q_emb = model.encode([test_query], normalize_embeddings=True)
    results = collection.query(query_embeddings=q_emb.tolist(), n_results=3)

    print(f"[VectorRAG] Top-3 results:")
    for j, (doc, dist) in enumerate(zip(results["documents"][0],
                                         results["distances"][0])):
        print(f"  [{j+1}] dist={dist:.4f} | source={results['metadatas'][0][j].get('source', '?')}")
        print(f"       {doc[:120]}...")

    print("\n[VectorRAG] ✓ Baseline ready for comparison.")


if __name__ == "__main__":
    main()
