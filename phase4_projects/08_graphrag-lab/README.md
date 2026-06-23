# P8: GraphRAG Lab — Knowledge Graph Retrieval Platform

> A production-grade experimental platform that implements the full Microsoft GraphRAG pipeline, benchmarked against traditional Vector RAG — all running locally on a MacBook with zero external embedding cost.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](./LICENSE)
[![Platform: macOS](https://img.shields.io/badge/platform-macOS%20Apple%20Silicon-silver)](https://www.apple.com/mac/)

---

## Overview

GraphRAG is Microsoft's approach to retrieval-augmented generation that builds a **knowledge graph** from documents — extracting entities, relationships, and hierarchical communities — then answers queries by traversing this structured representation instead of simple vector similarity.

This project provides a complete, runnable implementation that lets you:

- Run the **full GraphRAG pipeline** end-to-end (entity extraction → relationship extraction → Leiden community detection → community summarization → querying)
- Switch between **Global Search** (community-level thematic answers) and **Local Search** (entity-centric traversal)
- **Benchmark** GraphRAG against a Vector RAG baseline (Chroma + BGE-M3) side-by-side
- Keep everything **local and cost-efficient**: embeddings run on Metal/MPS at zero API cost; only the LLM step hits the DeepSeek API

### When to use GraphRAG vs Vector RAG

| Capability | GraphRAG | Vector RAG |
|:---|---:|:---|
| Multi-hop reasoning ("How are A, B, and C related?") | | |
| Global theme summarization | | |
| Entity-relationship queries | | |
| Factual lookups ("What is X?") | | |
| Keyword-heavy search | | |
| Query latency | ~3-10s | ~0.3-1s |
| Indexing time | 5-10 min (LLM) | 1-2 min |

---

## Architecture

```
data/raw/*.txt (52 Wikipedia + arXiv articles on AI/ML)
        │
        ▼
[Preprocessing]
  Clean, normalize, filter min 200 chars
        │
        ▼
data/input/*.txt
        │
        ▼
[GraphRAG Index Pipeline]                    [Embedding Service]
  ├─ Chunking                                 BGE-M3 on MPS/Metal
  ├─ Entity Extraction (DeepSeek API)         :19530 (OpenAI-compatible)
  ├─ Relationship Extraction (DeepSeek API)   Zero API cost
  ├─ Leiden Community Detection
  ├─ Community Summarization (DeepSeek API)
  └─ Text Embedding ←─────────────────────────┤
        │
        ▼
data/output/*.parquet (entities, relationships, communities, reports)
        │
        ├──▶ Global Search  — Community-level answers via map-reduce over reports
        └──▶ Local Search   — Entity-centric traversal via neighborhood expansion

Vector RAG (baseline):
data/input/*.txt → Chunking → BGE-M3 → Chroma → Cosine Similarity Search
```

### Design Decisions

| Decision | Rationale |
|:---------|:----------|
| **DeepSeek for LLM** | Accessible from China without VPN, JSON mode for entity extraction, ~$0.14/M tokens |
| **Local BGE-M3 embeddings** | Highest-volume API call (200-400/run); MPS eliminates cost and latency |
| **Separate embedding service** | GraphRAG expects OpenAI-compatible API; FastAPI wrapper bridges BGE-M3 |
| **Chroma for Vector RAG** | Lightweight, persistent, no external deps, fair comparison (same embeddings) |

---

## Quick Start

### Prerequisites

- macOS with Apple Silicon (M1+)
- [Miniforge](https://github.com/conda-forge/miniforge) (Conda)
- [DeepSeek API key](https://platform.deepseek.com/api_keys) (free tier is sufficient)

### One-command setup

```bash
# 1. Create conda env + install all dependencies + warm up BGE-M3
make setup

# 2. Download AI/ML corpus (50+ Wikipedia articles)
make download-corpus
make preprocess

# 3. Configure your API key
cp .env.example .env
# Edit .env → set GRAPHRAG_API_KEY=sk-your-deepseek-key

# 4. Initialize GraphRAG project
make init-graphrag
```

### Index & Query

```bash
# Terminal 1: Start BGE-M3 embedding service (keep running)
make run-embed

# Terminal 2: Run the full index pipeline (5-10 min)
make run-index

# Query!
make run-query-global    # Global search
make run-query-local     # Local search

# Compare with Vector RAG
make run-vector-rag
make compare

# Analyze index artifacts
make analyze
```

Alternatively, launch everything in a tmux session:

```bash
make run-all    # Starts embedding + index + query windows
make attach     # Attach to tmux session
make stop       # Kill everything
```

---

## Project Structure

```
08_graphrag-lab/
├── Makefile                      # One-command orchestration
├── pyproject.toml                # Package metadata & build config
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment variable template
├── runbook.md                    # Detailed troubleshooting guide
│
├── configs/
│   ├── settings.yaml             # Primary: DeepSeek API + local embeddings
│   └── settings.local.yaml       # Alternative: fully local with llama.cpp
│
├── data/
│   ├── raw/                      # Raw downloaded Wikipedia articles (52 topics)
│   ├── input/                    # Preprocessed .txt ready for indexing
│   ├── output/                   # GraphRAG index artifacts (*.parquet)
│   └── vector_store/             # Chroma vector database
│
├── src/graphrag_lab/
│   ├── serve_embedding.py        # BGE-M3 embedding API server (FastAPI)
│   ├── corpus.py                 # Corpus download & management
│   ├── querier.py                # Query interface for GraphRAG
│   └── comparator.py             # GraphRAG vs Vector RAG comparison engine
│
├── scripts/
│   ├── 00_check_env.py           # Environment verification
│   ├── 01_download_corpus.sh     # Corpus download script
│   ├── 02_preprocess_docs.py     # Document cleaning & normalization
│   ├── 03_init_graphrag.py       # GraphRAG project initialization
│   ├── 04_query_demo.py          # Query demo (global + local)
│   ├── 05_vector_rag_baseline.py # Vector RAG baseline builder
│   ├── 06_compare_rag.py         # Side-by-side benchmark
│   └── 07_analyze_artifacts.py   # Parquet artifact analyzer
│
├── prompts/
│   ├── entity_extraction.txt     # Custom entity extraction prompt
│   └── community_report.txt      # Custom community summarization prompt
│
├── tests/
│   ├── test_comparator.py        # Comparator unit tests
│   └── __init__.py
│
└── docs/
    ├── architecture.md           # System architecture & data flow
    └── comparison_report.md      # Generated benchmark report
```

---

## Configuration

### Environment Variables

| Variable | Required | Purpose |
|:---------|:--------:|:--------|
| `GRAPHRAG_API_KEY` | Yes | DeepSeek API key |
| `GRAPHRAG_EMBEDDING_API_BASE` | Yes | Local embedding service URL |
| `GRAPHRAG_EMBEDDING_API_KEY` | Yes | Embedding service auth (set to `local`) |
| `GRAPHRAG_EMBEDDING_MODEL` | Yes | Embedding model name (default: `bge-m3`) |
| `HF_ENDPOINT` | China | HuggingFace mirror endpoint |
| `NO_PROXY` | China | Bypass proxy for local services |

### GraphRAG Settings Files

| File | When to use |
|:-----|:------------|
| `configs/settings.yaml` | **Default** — DeepSeek API for LLM + local BGE-M3 for embeddings |
| `configs/settings.local.yaml` | **Fallback** — Fully local with llama.cpp server on :8081 |

---

## API Reference

### Python Package

```python
from graphrag_lab import CorpusDownloader, GraphRAGQuerier, RAGComparator

# Download & manage corpus
corpus = CorpusDownloader(output_dir="data/raw")
corpus.download_wikipedia("Knowledge_graph", language="en")

# Query GraphRAG
querier = GraphRAGQuerier(root_dir=".", method="global")
result = querier.ask("What are the main themes across all documents?")

# Compare GraphRAG vs Vector RAG
comparator = RAGComparator(
    graphrag_root=".",
    vector_store="data/vector_store",
    embedding_model="BAAI/bge-m3"
)
report = comparator.compare(["What is transfer learning?", "How does attention work?"])
```

### CLI

```bash
# Query demo
python scripts/04_query_demo.py --method global --query "Explain transformer architecture"

# Build Vector RAG baseline
python scripts/05_vector_rag_baseline.py --input data/input --embedding-model BAAI/bge-m3

# Run comparison benchmark
python scripts/06_compare_rag.py --output docs/comparison_report.md

# Analyze index artifacts
python scripts/07_analyze_artifacts.py
```

---

## Benchmarks

Representative results on a 52-document AI/ML corpus (MacBook Pro M5, 24GB RAM):

| Metric | GraphRAG Global | GraphRAG Local | Vector RAG |
|:---|---:|---:|---:|
| Query Latency | 5-10s | 3-6s | 0.3-1s |
| Indexing Time | 8 min | — | 1.5 min |
| Embedding Cost | $0 | $0 | $0 |
| LLM API Cost | ~$0.05/query | ~$0.03/query | ~$0.01/query |
| Multi-hop Accuracy | High | Medium-High | Low |
| Factual Precision | Medium | High | Very High |

---

## Troubleshooting

See [runbook.md](./runbook.md) for common issues including:
- Conda environment setup problems
- HuggingFace model download failures (China network)
- Embedding service connection errors
- GraphRAG index pipeline failures
- MPS/GPU memory management

Quick diagnostics:

```bash
make check-env                    # Verify environment
curl -s http://127.0.0.1:19530/health  # Check embedding service
```

---

## License

MIT © Chenxi
