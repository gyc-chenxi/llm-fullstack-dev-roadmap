.PHONY: setup clean test smoke run-all bench-10 bench-50 bench-100 eval-rag lint

# ============================================================
# AI-Gateway Makefile
# ============================================================

PYTHON = python
PIP = pip
UVICORN = uvicorn
BACKEND_DIR = backend
FRONTEND_DIR = frontend

# --- Environment Setup ---
setup:
	@echo "==> Installing backend dependencies..."
	cd $(BACKEND_DIR) && $(PIP) install -e ".[dev,test]"
	@echo "==> Installing frontend dependencies..."
	cd $(FRONTEND_DIR) && npm install
	@echo "==> Setup complete."

clean:
	@echo "==> Cleaning caches..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name *.egg-info -exec rm -rf {} + 2>/dev/null || true
	rm -rf $(BACKEND_DIR)/dist $(BACKEND_DIR)/build
	@echo "==> Clean complete."

# --- Testing ---
test:
	@echo "==> Running unit tests..."
	cd $(BACKEND_DIR) && $(PYTHON) -m pytest tests/unit/ -v

test-integration:
	@echo "==> Running integration tests..."
	cd $(BACKEND_DIR) && $(PYTHON) -m pytest tests/integration/ -v

test-all:
	@echo "==> Running all tests..."
	cd $(BACKEND_DIR) && $(PYTHON) -m pytest tests/ -v --cov=app --cov-report=term

lint:
	@echo "==> Running linter..."
	cd $(BACKEND_DIR) && ruff check app/

# --- Services ---
run-redis:
	@echo "==> Starting Redis..."
	docker-compose -f docker/docker-compose.yml up -d redis

run-backend:
	@echo "==> Starting FastAPI backend..."
	cd $(BACKEND_DIR) && $(UVICORN) app.main:app --host 0.0.0.0 --port 8000 --reload

run-frontend:
	@echo "==> Starting Vue 3 frontend..."
	cd $(FRONTEND_DIR) && npm run dev

run-all: run-redis
	@echo "==> Starting all services..."
	@echo "  Redis started, run 'make run-backend' and 'make run-frontend' in separate terminals"

# --- Smoke Test ---
smoke:
	@echo "==> Running smoke test..."
	curl -s -X POST http://localhost:8000/api/v1/chat \
		-H "Content-Type: application/json" \
		-d '{"messages":[{"role":"user","content":"Hello"}],"stream":true}' | head -20 || true
	@echo ""
	@echo "==> Checking health..."
	curl -s http://localhost:8000/api/v1/metrics/snapshot | python3 -m json.tool || true

# --- Benchmark ---
bench-10:
	@echo "==> Running 10-concurrency benchmark..."
	cd $(BACKEND_DIR) && $(PYTHON) -m pytest tests/e2e/test_benchmark.py::test_benchmark_10 -v -s

bench-50:
	@echo "==> Running 50-concurrency benchmark..."
	cd $(BACKEND_DIR) && $(PYTHON) -m pytest tests/e2e/test_benchmark.py::test_benchmark_50 -v -s

bench-100:
	@echo "==> Running 100-concurrency benchmark..."
	cd $(BACKEND_DIR) && $(PYTHON) -m pytest tests/e2e/test_benchmark.py::test_benchmark_100 -v -s

# --- RAG Eval ---
eval-rag:
	@echo "==> Running RAG evaluation..."
	cd $(BACKEND_DIR) && $(PYTHON) -m pytest tests/e2e/test_rag_eval.py -v -s

# --- Docker ---
docker-build:
	@echo "==> Building Docker images..."
	docker-compose -f docker/docker-compose.yml build

docker-up:
	@echo "==> Starting all Docker services..."
	docker-compose -f docker/docker-compose.yml up -d

docker-down:
	@echo "==> Stopping all Docker services..."
	docker-compose -f docker/docker-compose.yml down

# --- Help ---
help:
	@echo "AI-Gateway Makefile Commands:"
	@echo "  make setup           Install all dependencies"
	@echo "  make clean           Clean cache files"
	@echo "  make test            Run unit tests"
	@echo "  make test-integration Run integration tests"
	@echo "  make test-all        Run all tests with coverage"
	@echo "  make lint            Run linter"
	@echo "  make run-redis       Start Redis via Docker"
	@echo "  make run-backend     Start FastAPI backend"
	@echo "  make run-frontend    Start Vue 3 frontend"
	@echo "  make run-all         Start all services"
	@echo "  make smoke           Run smoke test"
	@echo "  make bench-10        Run 10-concurrency benchmark"
	@echo "  make bench-50        Run 50-concurrency benchmark"
	@echo "  make bench-100       Run 100-concurrency benchmark"
	@echo "  make eval-rag        Run RAG evaluation"
	@echo "  make docker-build    Build Docker images"
	@echo "  make docker-up       Start all Docker services"
	@echo "  make docker-down     Stop all Docker services"
