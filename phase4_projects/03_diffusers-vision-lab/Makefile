SHELL := /bin/bash

CONDA_ENV ?= cxllm
SESSION ?= diffusers_lab

ENGINE_HOST ?= 127.0.0.1
ENGINE_PORT ?= 8010
GATEWAY_HOST ?= 127.0.0.1
GATEWAY_PORT ?= 8020

DEFAULT_CONFIG ?= configs/sd15_txt2img.yaml
HF_HOME ?= $(PWD)/.cache/huggingface
PYTORCH_ENABLE_MPS_FALLBACK ?= 1

.PHONY: help setup check-env audit-models run-engine run-gateway run-all stop logs smoke test clean clean-outputs

help:
	@echo ""
	@echo "Diffusers Vision Lab"
	@echo "===================="
	@echo "make setup          Install dependencies"
	@echo "make check-env      Check Python/Torch/MPS"
	@echo "make audit-models   Audit local model directories"
	@echo "make run-engine     Run engine service"
	@echo "make run-gateway    Run gateway service"
	@echo "make run-all        Run engine + gateway in tmux"
	@echo "make smoke          Run txt2img smoke test through gateway"
	@echo "make stop           Stop tmux session"
	@echo "make logs           Attach tmux session"
	@echo "make test           Run pytest"
	@echo ""

setup:
	@eval "$$(conda shell.bash hook)" && \
	conda activate $(CONDA_ENV) && \
	python -m pip install --upgrade pip setuptools wheel && \
	python -m pip install -r requirements.txt

check-env:
	@eval "$$(conda shell.bash hook)" && \
	conda activate $(CONDA_ENV) && \
	python scripts/check_env.py

audit-models:
	@eval "$$(conda shell.bash hook)" && \
	conda activate $(CONDA_ENV) && \
	python scripts/audit_models.py

run-engine:
	@eval "$$(conda shell.bash hook)" && \
	conda activate $(CONDA_ENV) && \
	export HF_HOME="$(HF_HOME)" && \
	export PYTORCH_ENABLE_MPS_FALLBACK=$(PYTORCH_ENABLE_MPS_FALLBACK) && \
	python -m src.diffusers_lab.api \
		--host $(ENGINE_HOST) \
		--port $(ENGINE_PORT) \
		--default-config $(DEFAULT_CONFIG)

run-gateway:
	@eval "$$(conda shell.bash hook)" && \
	conda activate $(CONDA_ENV) && \
	python -m src.diffusers_lab.gateway \
		--host $(GATEWAY_HOST) \
		--port $(GATEWAY_PORT) \
		--engine-url http://$(ENGINE_HOST):$(ENGINE_PORT)

run-all:
	@tmux has-session -t $(SESSION) 2>/dev/null && tmux kill-session -t $(SESSION) || true
	@tmux new-session -d -s $(SESSION) -n engine \
		'cd $(PWD); eval "$$(conda shell.bash hook)"; conda activate $(CONDA_ENV); export HF_HOME="$(HF_HOME)"; export PYTORCH_ENABLE_MPS_FALLBACK=$(PYTORCH_ENABLE_MPS_FALLBACK); python -m src.diffusers_lab.api --host $(ENGINE_HOST) --port $(ENGINE_PORT) --default-config $(DEFAULT_CONFIG)'
	@tmux new-window -t $(SESSION):2 -n gateway \
		'cd $(PWD); eval "$$(conda shell.bash hook)"; conda activate $(CONDA_ENV); python -m src.diffusers_lab.gateway --host $(GATEWAY_HOST) --port $(GATEWAY_PORT) --engine-url http://$(ENGINE_HOST):$(ENGINE_PORT)'
	@echo "✅ Services started."
	@echo "Engine : http://$(ENGINE_HOST):$(ENGINE_PORT)"
	@echo "Gateway: http://$(GATEWAY_HOST):$(GATEWAY_PORT)"
	@echo "Attach : make logs"
	@echo "Stop   : make stop"

stop:
	@tmux has-session -t $(SESSION) 2>/dev/null && tmux kill-session -t $(SESSION) || true
	@echo "✅ stopped tmux session: $(SESSION)"

logs:
	@tmux attach -t $(SESSION)

smoke:
	@curl -X POST http://$(GATEWAY_HOST):$(GATEWAY_PORT)/v1/generate/txt2img \
		-H "Content-Type: application/json" \
		-d '{"prompt":"a cat wearing a wizard hat, cinematic lighting, detailed digital art","negative_prompt":"blurry, low quality, watermark, text","seed":42,"steps":25,"guidance_scale":7.5,"width":512,"height":512}' | python -m json.tool

test:
	@eval "$$(conda shell.bash hook)" && \
	conda activate $(CONDA_ENV) && \
	pytest -q

clean:
	@rm -rf .pytest_cache .ruff_cache
	@find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	@echo "✅ cleaned caches"

clean-outputs:
	@rm -rf outputs/images/* outputs/logs/* outputs/manifests/*
	@echo "✅ outputs cleaned"
