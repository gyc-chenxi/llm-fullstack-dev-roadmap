# P8 GraphRAG Lab — System Architecture

## Data Flow

```
data/raw/*.txt (Wikipedia + arXiv)
        │
        ▼
[02_preprocess_docs.py]
  Clean, normalize, filter min 200 chars
        │
        ▼
data/input/*.txt (standardized)
        │
        ▼
[graphrag index] ─────────────────────────────┐
  │                                            │
  ├─ create_base_text_units (chunking)         │
  ├─ extract_graph (LLM: entity + relation)    │  Embedding Service
  ├─ finalize_graph (dedup, merge)             │  (BGE-M3 on MPS)
  ├─ create_communities (Leiden)               │  :19530
  ├─ create_community_reports (LLM: summary)   │
  └─ generate_text_embeddings ────────────────┘
        │
        ▼
data/output/*.parquet
  ├─ entities.parquet
  ├─ relationships.parquet
  ├─ communities.parquet
  ├─ community_reports.parquet
  ├─ text_units.parquet
  └─ documents.parquet
        │
        ├──▶ [graphrag query --method global]  → Community-level answers
        └──▶ [graphrag query --method local]   → Entity-centric answers

Vector RAG (baseline):
data/input/*.txt → Chunking → BGE-M3 → Chroma → Cosine Similarity Search
```

## Component Diagram

```
┌──────────────────────────────────────────┐
│              DeepSeek API                  │
│         (Entity Extraction +              │
│          Community Summarization)          │
└────────────────┬─────────────────────────┘
                 │
┌────────────────┴─────────────────────────┐
│           Local Embedding Service          │
│         BGE-M3 on Apple M5 GPU            │
│         (OpenAI-compatible API)            │
└──────────────────────────────────────────┘
```

## Design Decisions

1. **Why DeepSeek for LLM?**  DeepSeek API is accessible from China without VPN, costs ~$0.14/M tokens, and supports JSON mode needed for entity extraction. GPT-4o-mini works too but requires VPN.

2. **Why local embeddings?**  Embedding generation is the highest-volume API call during indexing (200-400 calls). Running BGE-M3 locally on MPS eliminates this cost entirely and reduces latency.

3. **Why separate embedding service?**  GraphRAG expects an OpenAI-compatible API. Running a local FastAPI wrapper around BGE-M3 provides exactly that interface while keeping embeddings free and fast.

4. **Why Chroma for Vector RAG baseline?**  Lightweight, no external dependencies, persistent storage, cosine similarity support. Fair comparison since both systems use BGE-M3 embeddings.

5. **Why MPS over MLX?**  sentence-transformers has first-class MPS support. MLX via mlx-embedding exists but lacks the OpenAI-compatible server ecosystem.
