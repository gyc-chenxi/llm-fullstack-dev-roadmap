.PHONY: help setup start stop build serve gateway dev test bench metrics smoke clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-16s\033[0m %s\n", $$1, $$2}'

# ── One-command workflow ─────────────────────────────────────────────────────
setup: ## Check environment readiness (model, binary, deps)
	bash scripts/setup_check.sh

start: ## 🚀 One-command start: llama-server + Gateway + Frontend
	bash scripts/start_all.sh

stop: ## Stop all services
	bash scripts/stop_all.sh

# ── Individual services ──────────────────────────────────────────────────────
build: ## Compile llama.cpp (Metal, Release)
	bash scripts/build_llamacpp.sh

serve: ## Start llama-server only (port 8081)
	bash scripts/serve_q4.sh

gateway: ## Start FastAPI Gateway only (port 8000)
	uvicorn gateway.app:app --host 127.0.0.1 --port 8000 --reload

dev: ## Start Vue3 frontend only (port 5173)
	cd frontend/vue3-sse-demo && npm run dev

# ── Testing & observability ──────────────────────────────────────────────────
smoke: ## Quick curl smoke test
	bash scripts/smoke_openai.sh

test: ## Run unit + integration tests (23 tests)
	python -m pytest tests/ -v

bench: ## Run concurrency benchmark (2 concurrent, 10 requests)
	python scripts/bench_concurrency.py --concurrency 2 --requests 10 --max-tokens 256

metrics: ## Scrape llama-server /metrics snapshot
	python scripts/scrape_metrics.py

# ── Housekeeping ─────────────────────────────────────────────────────────────
clean: ## Remove Python cache and logs
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete 2>/dev/null || true
	rm -rf logs/ .pids 2>/dev/null || true
