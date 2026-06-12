SHELL := /bin/bash

PROJECT_NAME := 04_sam2-vision-segmentation-lab
PYTHON := python
PIP := python -m pip

API_HOST ?= 127.0.0.1
API_PORT ?= 8004
GRADIO_PORT ?= 7864

IMAGE ?= data/images/sample_01.jpg
MASK ?= outputs/masks/sample_01_point_mask.png

X ?= 400
Y ?= 300
LABEL ?= 1

X1 ?= 100
Y1 ?= 80
X2 ?= 700
Y2 ?= 600

PROMPT ?= a clean futuristic product design background, soft studio lighting

HF_ENDPOINT ?= https://hf-mirror.com
HF_HOME ?= $(PWD)/.cache/huggingface
HF_HUB_CACHE ?= $(PWD)/.cache/huggingface/hub
HF_XET_HIGH_PERFORMANCE ?= 1

SAM2_REPO := external/sam2
SAM2_CKPT_DIR := models/sam2/checkpoints
SAM2_TINY_CKPT := $(SAM2_CKPT_DIR)/sam2.1_hiera_tiny.pt
SAM2_TINY_URL := https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_tiny.pt

.PHONY: help
help:
	@echo ""
	@echo "$(PROJECT_NAME) commands:"
	@echo "  make setup              Install dependencies and SAM2"
	@echo "  make check-env          Check Python/PyTorch/MPS/SAM2"
	@echo "  make download-models    Download SAM2 + Diffusers models"
	@echo "  make api                Start FastAPI service"
	@echo "  make ui                 Start Gradio UI"
	@echo "  make run-all            Start API + UI with nohup"
	@echo "  make stop               Stop background services"
	@echo "  make segment-point      Run point prompt segmentation"
	@echo "  make segment-box        Run box prompt segmentation"
	@echo "  make segment-auto       Run automatic mask generation"
	@echo "  make inpaint            Run SAM2 mask + Diffusers inpaint"
	@echo "  make video-track        Run SAM2 video tracking demo"
	@echo "  make test               Run tests"
	@echo "  make lint               Run ruff"
	@echo "  make clean              Clean outputs/cache"
	@echo ""

.PHONY: setup
setup:
	@echo "[setup] Python:"
	@$(PYTHON) --version
	@echo "[setup] Installing base dependencies..."
	@$(PIP) install -U pip setuptools wheel
	@$(PIP) install -r requirements.txt
	@echo "[setup] Installing SAM2..."
	@mkdir -p external
	@if [ ! -d "$(SAM2_REPO)" ]; then \
		git clone https://github.com/facebookresearch/sam2.git $(SAM2_REPO); \
	else \
		cd $(SAM2_REPO) && git pull; \
	fi
	@cd $(SAM2_REPO) && SAM2_BUILD_CUDA=0 $(PIP) install -e ".[notebooks]"
	@echo "[setup] Done."

.PHONY: check-env
check-env:
	@$(PYTHON) scripts/00_check_env.py

.PHONY: download-models
download-models: download-sam2 download-diffusers

.PHONY: download-sam2
download-sam2:
	@mkdir -p $(SAM2_CKPT_DIR)
	@if [ ! -f "$(SAM2_TINY_CKPT)" ]; then \
		echo "[download] Downloading SAM2 tiny checkpoint..."; \
		curl -L -o $(SAM2_TINY_CKPT) $(SAM2_TINY_URL); \
	else \
		echo "[download] SAM2 checkpoint exists: $(SAM2_TINY_CKPT)"; \
	fi

.PHONY: download-diffusers
download-diffusers:
	@echo "[download] Downloading Diffusers inpaint model via HF mirror..."
	@mkdir -p models/diffusers/stable-diffusion-inpainting
	@HF_ENDPOINT=$(HF_ENDPOINT) \
	HF_HOME=$(HF_HOME) \
	HF_HUB_CACHE=$(HF_HUB_CACHE) \
	HF_XET_HIGH_PERFORMANCE=$(HF_XET_HIGH_PERFORMANCE) \
	hf download runwayml/stable-diffusion-inpainting \
		--local-dir models/diffusers/stable-diffusion-inpainting \
		--include "*.json" "*.txt" "*.safetensors" "*.bin" || true
	@echo "[download] Diffusers model download step finished."

.PHONY: api
api:
	@PYTHONPATH=src \
	uvicorn sam2_lab.api.server:app \
	  --host $(API_HOST) \
	  --port $(API_PORT) \
	  --reload

.PHONY: ui
ui:
	@PYTHONPATH=src \
	$(PYTHON) -m sam2_lab.app \
	  --host $(API_HOST) \
	  --port $(GRADIO_PORT)

.PHONY: run-all
run-all:
	@mkdir -p outputs/logs outputs/pids
	@echo "[run-all] Starting API on $(API_HOST):$(API_PORT)"
	@PYTHONPATH=src nohup uvicorn sam2_lab.api.server:app \
	  --host $(API_HOST) \
	  --port $(API_PORT) \
	  > outputs/logs/api.log 2>&1 & echo $$! > outputs/pids/api.pid
	@sleep 2
	@echo "[run-all] Starting UI on $(API_HOST):$(GRADIO_PORT)"
	@PYTHONPATH=src nohup $(PYTHON) -m sam2_lab.app \
	  --host $(API_HOST) \
	  --port $(GRADIO_PORT) \
	  > outputs/logs/ui.log 2>&1 & echo $$! > outputs/pids/ui.pid
	@echo "[run-all] Services started."
	@echo "[run-all] API: http://$(API_HOST):$(API_PORT)"
	@echo "[run-all] UI : http://$(API_HOST):$(GRADIO_PORT)"
	@echo "[run-all] Logs: tail -f outputs/logs/api.log outputs/logs/ui.log"
	@echo "[run-all] Stop: make stop"

.PHONY: stop
stop:
	@echo "[stop] Stopping background services..."
	@if [ -f outputs/pids/api.pid ]; then kill $$(cat outputs/pids/api.pid) 2>/dev/null || true; rm -f outputs/pids/api.pid; fi
	@if [ -f outputs/pids/ui.pid ]; then kill $$(cat outputs/pids/ui.pid) 2>/dev/null || true; rm -f outputs/pids/ui.pid; fi
	@echo "[stop] Done."

.PHONY: segment-point
segment-point:
	@PYTHONPATH=src $(PYTHON) scripts/02_segment_point.py \
	  --image $(IMAGE) \
	  --x $(X) \
	  --y $(Y) \
	  --label $(LABEL)

.PHONY: segment-box
segment-box:
	@PYTHONPATH=src $(PYTHON) scripts/03_segment_box.py \
	  --image $(IMAGE) \
	  --x1 $(X1) \
	  --y1 $(Y1) \
	  --x2 $(X2) \
	  --y2 $(Y2)

.PHONY: segment-auto
segment-auto:
	@PYTHONPATH=src $(PYTHON) scripts/04_segment_auto.py \
	  --image $(IMAGE)

.PHONY: quality
quality:
	@PYTHONPATH=src $(PYTHON) scripts/05_mask_quality_report.py \
	  --mask $(MASK)

.PHONY: inpaint
inpaint:
	@PYTHONPATH=src $(PYTHON) scripts/06_sam2_inpaint.py \
	  --image $(IMAGE) \
	  --mask $(MASK) \
	  --prompt "$(PROMPT)"

.PHONY: video-track
video-track:
	@PYTHONPATH=src $(PYTHON) scripts/07_video_track.py \
	  --video data/videos/sample_video.mp4 \
	  --x $(X) \
	  --y $(Y)

.PHONY: smoke
smoke:
	@PYTHONPATH=src $(PYTHON) scripts/99_smoke_test.py

.PHONY: test
test:
	@PYTHONPATH=src pytest -q tests

.PHONY: lint
lint:
	@ruff check src scripts tests

.PHONY: format
format:
	@ruff format src scripts tests

.PHONY: clean
clean:
	@echo "[clean] Removing outputs and caches..."
	@rm -rf outputs/masks/* outputs/overlays/* outputs/inpaint/* outputs/video/* outputs/reports/* outputs/manifests/*
	@rm -rf .pytest_cache .ruff_cache
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo "[clean] Done."

.PHONY: clean-models
clean-models:
	@echo "[clean-models] Removing local model files..."
	@rm -rf models/sam2/checkpoints/*
	@rm -rf models/diffusers/*
	@echo "[clean-models] Done."