.PHONY: help setup start stop server dev clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-16s\033[0m %s\n", $$1, $$2}'

# ── One-command workflow ─────────────────────────────────────────────────────
setup: ## Check environment readiness (model, deps, npm)
	bash scripts/setup_check.sh

start: ## 🚀 One-command start: Server (MLX) + Frontend
	bash scripts/start_all.sh

stop: ## Stop all services
	bash scripts/stop_all.sh

# ── Individual services ──────────────────────────────────────────────────────
server: ## Start FastAPI server only (port 8001)
	cd server && python -m uvicorn app:app --host 0.0.0.0 --port 8001 --reload

dev: ## Start Vue3 frontend only (port 5173)
	cd frontend && npm run dev

# ── Model ────────────────────────────────────────────────────────────────────
download-model: ## Download Qwen2.5-7B-Instruct-4bit MLX model
	python scripts/download_model.py

# ── Housekeeping ─────────────────────────────────────────────────────────────
clean: ## Remove Python cache and logs
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete 2>/dev/null || true
	rm -rf logs/ .pids 2>/dev/null || true
