SHELL := /bin/bash

CONDA_ENV := cxllm
PYTHON := conda run -n $(CONDA_ENV) python
PIP := conda run -n $(CONDA_ENV) python -m pip

PROJECT_ROOT := $(shell pwd)
PYTHONPATH_VALUE := $(PROJECT_ROOT)/src:$(PROJECT_ROOT)

QWEN25_MODEL := models/Qwen2.5-VL-3B-Instruct
QWEN2_MODEL := models/Qwen2-VL-2B-Instruct
LLAVA_MODEL := models/llava-onevision-qwen2-0.5b-si-hf

ENGINE_PORT := 8001
GATEWAY_PORT := 8000
TMUX_SESSION := p5-vlm

.PHONY: help setup env-check download-qwen25 download-qwen2 download-llava download-all \
        run-engine run-gateway run-all stop logs test lint clean clean-models clean-cache

help:
	@echo ""
	@echo "P5 VLM Understanding Lab"
	@echo ""
	@echo "Available commands:"
	@echo "  make setup           Install Python dependencies into Conda env: $(CONDA_ENV)"
	@echo "  make env-check       Print Python / Torch / MPS environment"
	@echo "  make download-qwen25 Download Qwen2.5-VL-3B-Instruct"
	@echo "  make download-qwen2  Download Qwen2-VL-2B-Instruct fallback"
	@echo "  make download-llava  Download LLaVA-OneVision 0.5B"
	@echo "  make download-all    Download all recommended models"
	@echo "  make run-engine      Run Qwen-VL engine on port $(ENGINE_PORT)"
	@echo "  make run-gateway     Run FastAPI gateway on port $(GATEWAY_PORT)"
	@echo "  make run-all         Start engine + gateway in tmux"
	@echo "  make stop            Stop tmux session"
	@echo "  make logs            Attach tmux session"
	@echo "  make test            Run pytest"
	@echo "  make lint            Run ruff"
	@echo "  make clean           Clean tmp/cache/output files"
	@echo "  make clean-models    Remove downloaded model files"
	@echo ""

setup:
	$(PIP) install -U pip setuptools wheel
	$(PIP) install -r requirements.txt

env-check:
	PYTHONPATH=$(PYTHONPATH_VALUE) \
	$(PYTHON) scripts/print_env.py

download-qwen25:
	mkdir -p models
	HF_HUB_ENABLE_HF_TRANSFER=1 HF_HOME=$(PROJECT_ROOT)/.cache/huggingface \
	conda run -n $(CONDA_ENV) hf download Qwen/Qwen2.5-VL-3B-Instruct \
		--local-dir $(QWEN25_MODEL)

download-qwen2:
	mkdir -p models
	HF_HUB_ENABLE_HF_TRANSFER=1 HF_HOME=$(PROJECT_ROOT)/.cache/huggingface \
	conda run -n $(CONDA_ENV) hf download Qwen/Qwen2-VL-2B-Instruct \
		--local-dir $(QWEN2_MODEL)

download-llava:
	mkdir -p models
	HF_HUB_ENABLE_HF_TRANSFER=1 HF_HOME=$(PROJECT_ROOT)/.cache/huggingface \
	conda run -n $(CONDA_ENV) hf download llava-hf/llava-onevision-qwen2-0.5b-si-hf \
		--local-dir $(LLAVA_MODEL)

download-all: download-qwen25 download-qwen2 download-llava

run-engine:
	PYTHONPATH=$(PYTHONPATH_VALUE) \
	PYTORCH_ENABLE_MPS_FALLBACK=1 \
	TOKENIZERS_PARALLELISM=false \
	HF_HOME=$(PROJECT_ROOT)/.cache/huggingface \
	MODEL_PATH=$(QWEN25_MODEL) \
	MODEL_BACKEND=qwen2_5_vl \
	MAX_NEW_TOKENS=512 \
	MAX_PIXELS=786432 \
	$(PYTHON) scripts/serve_qwen_vl.py

run-gateway:
	PYTHONPATH=$(PYTHONPATH_VALUE) \
	PYTORCH_ENABLE_MPS_FALLBACK=1 \
	TOKENIZERS_PARALLELISM=false \
	$(PYTHON) -m vlm_p5.gateway

run-all:
	@command -v tmux >/dev/null 2>&1 || { echo "tmux not found. Install with: brew install tmux"; exit 1; }
	@tmux has-session -t $(TMUX_SESSION) 2>/dev/null && { echo "tmux session $(TMUX_SESSION) already exists. Run: make logs"; exit 0; } || true
	@tmux new-session -d -s $(TMUX_SESSION) -n engine
	@tmux send-keys -t $(TMUX_SESSION):engine "cd $(PROJECT_ROOT) && make run-engine" C-m
	@sleep 8
	@tmux new-window -t $(TMUX_SESSION) -n gateway
	@tmux send-keys -t $(TMUX_SESSION):gateway "cd $(PROJECT_ROOT) && make run-gateway" C-m
	@tmux new-window -t $(TMUX_SESSION) -n curl
	@tmux send-keys -t $(TMUX_SESSION):curl "cd $(PROJECT_ROOT) && echo 'Engine: http://127.0.0.1:$(ENGINE_PORT)/health' && echo 'Gateway: http://127.0.0.1:$(GATEWAY_PORT)/health'" C-m
	@echo "Started tmux session: $(TMUX_SESSION)"
	@echo "Attach logs: make logs"
	@echo "Stop services: make stop"

stop:
	@tmux kill-session -t $(TMUX_SESSION) 2>/dev/null || true
	@echo "Stopped tmux session: $(TMUX_SESSION)"

logs:
	tmux attach -t $(TMUX_SESSION)

test:
	PYTHONPATH=$(PYTHONPATH_VALUE) \
	$(PYTHON) -m pytest -q

lint:
	PYTHONPATH=$(PYTHONPATH_VALUE) \
	$(PYTHON) -m ruff check src scripts tests

clean:
	rm -rf tmp
	rm -rf outputs/responses/* outputs/reverse_prompts/* outputs/benchmark/*
	rm -rf .pytest_cache .ruff_cache
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +

clean-cache:
	rm -rf .cache/huggingface

clean-models:
	rm -rf models/*
	touch models/.gitkeep