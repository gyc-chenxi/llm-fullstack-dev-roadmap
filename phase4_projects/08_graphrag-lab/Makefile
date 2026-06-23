SHELL := /bin/bash

PROJECT_NAME := graphrag-lab
CONDA_ENV ?= cxllm

PY := PYTHONPATH=. conda run -n $(CONDA_ENV) python
PIP := conda run -n $(CONDA_ENV) python -m pip

EMBED_HOST ?= 127.0.0.1
EMBED_PORT ?= 19530
LLM_HOST ?= 127.0.0.1
LLM_PORT ?= 8081

TMUX_SESSION ?= p8-graphrag
GRAPH_ROOT ?= .

.PHONY: help
help:
	@echo ""
	@echo "P8 GraphRAG Lab - Knowledge Graph Retrieval"
	@echo ""
	@echo "Available commands:"
	@echo "  make setup              Create conda env + install all dependencies"
	@echo "  make check-env          Verify Python/Conda/MPS/API Key"
	@echo "  make download-corpus    Download AI/ML corpus (Wikipedia + arXiv)"
	@echo "  make preprocess         Clean and normalize documents"
	@echo "  make init-graphrag      Initialize GraphRAG project config"
	@echo "  make run-embed          Start local BGE-M3 embedding service"
	@echo "  make run-index          Run GraphRAG index pipeline"
	@echo "  make run-query-global   Execute Global Search query"
	@echo "  make run-query-local    Execute Local Search query"
	@echo "  make run-vector-rag     Build Vector RAG baseline (Chroma)"
	@echo "  make compare            GraphRAG vs Vector RAG benchmark"
	@echo "  make analyze            Analyze index artifacts (parquet)"
	@echo "  make run-all            Start full pipeline in tmux"
	@echo "  make attach             Attach to tmux session"
	@echo "  make stop               Stop all services"
	@echo "  make clean              Remove index artifacts and cache"
	@echo ""

.PHONY: setup
setup:
	@echo "[setup] checking conda env: $(CONDA_ENV)"
	@conda info --envs | awk '{print $$1}' | grep -qx "$(CONDA_ENV)" || conda create -n $(CONDA_ENV) python=3.11 -y
	@echo "[setup] upgrading pip"
	@$(PIP) install -U pip setuptools wheel
	@echo "[setup] installing PyTorch nightly (MPS)"
	@$(PIP) install torch torchvision --index-url https://download.pytorch.org/whl/nightly/cpu
	@echo "[setup] installing project dependencies"
	@$(PIP) install -U -r requirements.txt
	@echo "[setup] installing hf-transfer"
	@$(PIP) install -U hf-transfer
	@echo "[setup] persisting HF_ENDPOINT to conda env"
	@conda env config vars set -n $(CONDA_ENV) HF_ENDPOINT=https://hf-mirror.com || true
	@echo "[setup] warming up BGE-M3 (first run downloads ~2.2GB)..."
	@HF_ENDPOINT=https://hf-mirror.com HF_HUB_ENABLE_HF_TRANSFER=1 $(PY) - <<'PY'
from sentence_transformers import SentenceTransformer
m = SentenceTransformer("BAAI/bge-m3", device="mps")
print(f"BGE-M3 ready: dim={m.get_sentence_embedding_dimension()}")
PY
	@echo "[setup] done"

.PHONY: check-env
check-env:
	@$(PY) scripts/00_check_env.py

.PHONY: download-corpus
download-corpus:
	@echo "[corpus] downloading AI/ML corpus..."
	@mkdir -p data/raw data/input data/output data/vector_store logs
	@PYTHONPATH=. bash scripts/01_download_corpus.sh
	@echo "[corpus] done"

.PHONY: preprocess
preprocess:
	@echo "[preprocess] cleaning documents..."
	@$(PY) scripts/02_preprocess_docs.py --input data/raw --output data/input

.PHONY: init-graphrag
init-graphrag:
	@echo "[init] initializing GraphRAG project..."
	@$(PY) scripts/03_init_graphrag.py

.PHONY: run-embed
run-embed:
	@echo "[embed] BGE-M3 embedding service on :$(EMBED_PORT)"
	@echo "[embed] Verify: curl -s http://$(EMBED_HOST):$(EMBED_PORT)/health"
	@$(PY) src/graphrag_lab/serve_embedding.py --host $(EMBED_HOST) --port $(EMBED_PORT) --model BAAI/bge-m3 --device mps

.PHONY: run-index
run-index:
	@echo "[index] checking embedding service..."
	@curl -sf http://$(EMBED_HOST):$(EMBED_PORT)/health > /dev/null || \
		(echo "ERROR: Embedding service not running on :$(EMBED_PORT). Start with: make run-embed" && exit 1)
	@echo "[index] embedding service OK, running GraphRAG pipeline (5-10 min)..."
	@$(PY) -m graphrag index --root $(GRAPH_ROOT)
	@echo "[index] done. artifacts in data/output/"
	@ls -lh data/output/*.parquet 2>/dev/null || echo "check data/output/"

.PHONY: run-query-global
run-query-global:
	@$(PY) scripts/04_query_demo.py --method global

.PHONY: run-query-local
run-query-local:
	@$(PY) scripts/04_query_demo.py --method local

.PHONY: run-vector-rag
run-vector-rag:
	@$(PY) scripts/05_vector_rag_baseline.py --input data/input --vector-store data/vector_store --embedding-model BAAI/bge-m3 --chunk-size 1200 --chunk-overlap 100

.PHONY: compare
compare:
	@$(PY) scripts/06_compare_rag.py --graphrag-root $(GRAPH_ROOT) --vector-store data/vector_store --embedding-model BAAI/bge-m3 --output docs/comparison_report.md

.PHONY: analyze
analyze:
	@$(PY) scripts/07_analyze_artifacts.py

.PHONY: run-all
run-all:
	@echo "[run-all] starting services in tmux: $(TMUX_SESSION)"
	@tmux has-session -t $(TMUX_SESSION) 2>/dev/null && tmux kill-session -t $(TMUX_SESSION) || true
	@tmux new-session -d -s $(TMUX_SESSION) -n embed "make run-embed"
	@tmux new-window -t $(TMUX_SESSION):1 -n index "sleep 10 && echo 'Embedding ready. Run: make run-index'; bash"
	@tmux new-window -t $(TMUX_SESSION):2 -n query "sleep 15 && echo 'Ready. Run: make run-query-global or make compare'; bash"
	@echo ""
	@echo "tmux session: $(TMUX_SESSION)"
	@echo "  Window 0 (embed): BGE-M3 embedding service"
	@echo "  Window 1 (index): GraphRAG index pipeline"
	@echo "  Window 2 (query): Query & compare"
	@echo ""
	@echo "  make attach   — attach to session"
	@echo "  make stop     — kill everything"
	@echo ""

.PHONY: attach
attach:
	@tmux attach -t $(TMUX_SESSION)

.PHONY: stop
stop:
	@echo "[stop] killing tmux session: $(TMUX_SESSION)"
	@tmux kill-session -t $(TMUX_SESSION) 2>/dev/null || true
	@echo "[stop] killing embedding service on :$(EMBED_PORT)..."
	@lsof -ti:$(EMBED_PORT) | xargs kill -9 2>/dev/null || true
	@echo "[stop] done"

.PHONY: clean
clean: stop
	@echo "[clean] removing artifacts and cache..."
	@rm -rf data/output/*.parquet data/output/*.json data/output/*.graphml
	@rm -rf data/vector_store/*
	@rm -rf logs/* cache/
	@rm -rf .pytest_cache .ruff_cache
	@find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	@mkdir -p data/output data/vector_store logs
	@touch data/output/.gitkeep data/vector_store/.gitkeep logs/.gitkeep
	@echo "[clean] done"

.PHONY: nuke
nuke: clean
	@echo "[nuke] removing models and conda env..."
	@rm -rf models/
	@conda env remove -n $(CONDA_ENV) -y 2>/dev/null || true
	@echo "[nuke] everything destroyed. Run 'make setup' to rebuild."
