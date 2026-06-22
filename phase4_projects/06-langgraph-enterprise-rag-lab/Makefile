SHELL := /bin/bash

PROJECT_NAME := langgraph-enterprise-rag
CONDA_ENV ?= cxllm

PY := PYTHONPATH=. conda run -n $(CONDA_ENV) python
PIP := conda run -n $(CONDA_ENV) python -m pip

LLM_HOST ?= 127.0.0.1
LLM_PORT ?= 8080
API_HOST ?= 127.0.0.1
API_PORT ?= 8006

TMUX_SESSION ?= p6-rag

MODEL_REPO ?= Qwen/Qwen2.5-7B-Instruct-GGUF
MODEL_DIR ?= models/llm/qwen2.5-7b-instruct-gguf
MODEL_FILE ?= $(MODEL_DIR)/qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf

CHROMA_DIR ?= data/chroma
CHECKPOINT_DB ?= data/checkpoints/langgraph.sqlite

.PHONY: help
help:
	@echo ""
	@echo "P6 LangGraph Enterprise RAG"
	@echo ""
	@echo "Available commands:"
	@echo "  make setup             Create/update Conda env and install dependencies"
	@echo "  make install-llama     Install llama-cpp-python with Metal backend"
	@echo "  make download-models   Download local LLM and warm up embedding/reranker"
	@echo "  make check-env         Check Python, Conda, Torch MPS"
	@echo "  make download-data     Download sample open-source documents"
	@echo "  make ingest            Build Chroma + BM25 index from data/raw"
	@echo "  make run-llm           Start local OpenAI-compatible LLM server"
	@echo "  make run-api           Start FastAPI RAG gateway"
	@echo "  make run-all           Start LLM + API in tmux"
	@echo "  make attach            Attach tmux session"
	@echo "  make stop              Stop tmux session"
	@echo "  make smoke             Run smoke tests"
	@echo "  make test              Run pytest"
	@echo "  make lint              Run ruff"
	@echo "  make clean             Remove runtime data, checkpoints, cache, and models"
	@echo ""

.PHONY: setup
setup:
	@echo "[setup] checking conda env: $(CONDA_ENV)"
	@conda info --envs | awk '{print $$1}' | grep -qx "$(CONDA_ENV)" || conda create -n $(CONDA_ENV) python=3.11 -y
	@echo "[setup] installing build tools"
	@conda install -n $(CONDA_ENV) -c conda-forge cmake ninja pkg-config -y
	@echo "[setup] upgrading pip"
	@$(PIP) install -U pip setuptools wheel
	@echo "[setup] installing python requirements"
	@$(PIP) install -U -r requirements.txt
	@echo "[setup] done"

.PHONY: install-llama
install-llama:
	@echo "[llama] installing llama-cpp-python with Metal backend"
	@CMAKE_ARGS="-DGGML_METAL=on" FORCE_CMAKE=1 conda run -n $(CONDA_ENV) python -m pip install -U --no-cache-dir "llama-cpp-python[server]"
	@echo "[llama] done"

.PHONY: download-models
download-models:
	@echo "[models] downloading Qwen2.5 7B Instruct GGUF Q4_K_M"
	@mkdir -p $(MODEL_DIR)
	@conda run -n $(CONDA_ENV) hf download $(MODEL_REPO) \
		--local-dir $(MODEL_DIR) \
		--include "qwen2.5-7b-instruct-q4_k_m-*.gguf"
	@echo "[models] warming up embedding model"
	@$(PY) - <<'PY'
from sentence_transformers import SentenceTransformer
SentenceTransformer("BAAI/bge-m3")
print("embedding model ready")
PY
	@echo "[models] warming up reranker model"
	@$(PY) - <<'PY'
from FlagEmbedding import FlagReranker
FlagReranker("BAAI/bge-reranker-v2-m3", use_fp16=False)
print("reranker model ready")
PY
	@echo "[models] done"

.PHONY: download-data
download-data:
	@echo "[data] downloading sample open-source documents"
	@mkdir -p data/raw
	@curl -L -o data/raw/RAG_Survey.pdf https://arxiv.org/pdf/2312.10997.pdf
	@curl -L -o data/raw/Attention_Is_All_You_Need.pdf https://arxiv.org/pdf/1706.03762.pdf
	@curl -L -o data/raw/qwen2.5_readme_zh.md https://raw.githubusercontent.com/QwenLM/Qwen2.5/main/README_CN.md
	@ls -lh data/raw/
	@echo "[data] done"

.PHONY: check-env
check-env:
	@$(PY) scripts/00_check_env.py

.PHONY: ingest
ingest:
	@echo "[ingest] building local index"
	@mkdir -p data/raw data/processed data/chroma
	@$(PY) scripts/02_ingest_docs.py \
		--input data/raw \
		--chroma-dir $(CHROMA_DIR) \
		--collection enterprise_rag_docs
	@echo "[ingest] done"

.PHONY: run-llm
run-llm:
	@echo "[llm] starting llama.cpp OpenAI-compatible server"
	@$(PY) -m llama_cpp.server \
		--model $(MODEL_FILE) \
		--host $(LLM_HOST) \
		--port $(LLM_PORT) \
		--n_ctx 8192 \
		--n_gpu_layers -1 \
		--n_batch 512 \
		--chat_format chatml

.PHONY: run-api
run-api:
	@echo "[api] starting FastAPI gateway"
	@OPENAI_API_BASE=http://$(LLM_HOST):$(LLM_PORT)/v1 \
	OPENAI_API_KEY=local \
	OPENAI_MODEL=local-qwen2.5-7b-instruct \
	CHROMA_DIR=$(CHROMA_DIR) \
	CHECKPOINT_DB=$(CHECKPOINT_DB) \
	conda run -n $(CONDA_ENV) uvicorn src.langgraph_enterprise_rag.api.main:app \
		--host $(API_HOST) \
		--port $(API_PORT) \
		--reload

.PHONY: run-all
run-all:
	@echo "[run-all] starting services in tmux session: $(TMUX_SESSION)"
	@tmux has-session -t $(TMUX_SESSION) 2>/dev/null && tmux kill-session -t $(TMUX_SESSION) || true
	@tmux new-session -d -s $(TMUX_SESSION) -n llm "make run-llm"
	@tmux new-window -t $(TMUX_SESSION):1 -n api "sleep 8 && make run-api"
	@tmux new-window -t $(TMUX_SESSION):2 -n smoke "sleep 15 && make smoke; bash"
	@echo ""
	@echo "Services started."
	@echo "  LLM: http://$(LLM_HOST):$(LLM_PORT)"
	@echo "  API: http://$(API_HOST):$(API_PORT)"
	@echo ""
	@echo "Attach logs:"
	@echo "  make attach"
	@echo ""
	@echo "Stop services:"
	@echo "  make stop"
	@echo ""

.PHONY: attach
attach:
	@tmux attach -t $(TMUX_SESSION)

.PHONY: stop
stop:
	@echo "[stop] stopping tmux session: $(TMUX_SESSION)"
	@tmux kill-session -t $(TMUX_SESSION) 2>/dev/null || true

.PHONY: smoke
smoke:
	@echo "[smoke] checking API health"
	@curl -fsS http://$(API_HOST):$(API_PORT)/health | python -m json.tool --no-ensure-ascii
	@echo "[smoke] checking RAG invoke"
	@curl -fsS http://$(API_HOST):$(API_PORT)/v1/rag/invoke \
		-H "Content-Type: application/json" \
		-d '{"query":"请用一句话说明知识库主题","thread_id":"smoke-001"}' \
		| python -m json.tool --no-ensure-ascii

.PHONY: test
test:
	@$(PY) -m pytest -q

.PHONY: lint
lint:
	@$(PY) -m ruff check src tests scripts

.PHONY: clean
clean: stop
	@echo "[clean] removing runtime data, cache, checkpoints, and models"
	@rm -rf data/chroma data/processed data/checkpoints
	@rm -rf models/llm models/embedding models/reranker
	@rm -rf .pytest_cache .ruff_cache
	@find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	@mkdir -p data/raw data/processed data/chroma data/checkpoints models/llm models/embedding models/reranker
	@touch data/processed/.gitkeep data/chroma/.gitkeep data/checkpoints/.gitkeep
	@touch models/llm/.gitkeep models/embedding/.gitkeep models/reranker/.gitkeep
	@echo "[clean] done"