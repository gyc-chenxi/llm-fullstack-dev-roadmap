#!/usr/bin/env bash
set -euo pipefail

# ──────────────────────────────────────────────────────────────────────────────
# start_all.sh — one-command launcher for the full MLX Chat stack.
#
# Usage:
#   ./scripts/start_all.sh              # Full stack (server + frontend)
#   ./scripts/start_all.sh --no-frontend # Server only, frontend you start manually
#
# What it does:
#   1. Validates prerequisites (model dir, deps, ports)
#   2. Starts FastAPI server (with MLX model loading) in background → logs/server.log
#   3. Waits for server /health to return 200 (model loading takes ~10-30s)
#   4. Starts Vue3 frontend in foreground (Ctrl+C stops everything)
#   5. On exit (Ctrl+C or error), cleans up all child processes
# ──────────────────────────────────────────────────────────────────────────────

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PIDS_FILE="$ROOT_DIR/.pids"
LOG_DIR="$ROOT_DIR/logs"
MODEL_DIR="${ROOT_DIR}/models/Qwen2.5-7B-Instruct-4bit"
SERVER_DIR="${ROOT_DIR}/server"

START_FRONTEND=true
if [[ "${1:-}" == "--no-frontend" ]]; then
    START_FRONTEND=false
fi

# ── Colour helpers ────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info()  { printf "${GREEN}[INFO]${NC}  %s\n" "$*"; }
log_warn()  { printf "${YELLOW}[WARN]${NC}  %s\n" "$*"; }
log_error() { printf "${RED}[ERROR]${NC} %s\n" "$*"; }
log_step()  { printf "\n${CYAN}━━━ %s ━━━${NC}\n" "$*"; }

# ── Cleanup on exit ──────────────────────────────────────────────────────────
cleanup() {
    log_info "Shutting down all services..."
    if [[ -f "$PIDS_FILE" ]]; then
        while read -r pid; do
            if kill -0 "$pid" 2>/dev/null; then
                kill "$pid" 2>/dev/null || true
                log_info "Stopped PID $pid"
            fi
        done < "$PIDS_FILE"
        rm -f "$PIDS_FILE"
    fi
    # Belt-and-suspenders.
    pkill -f "uvicorn.*server.app" 2>/dev/null || true
    pkill -f "vite.*5173" 2>/dev/null || true
    log_info "All services stopped.  Goodbye!"
}
trap cleanup EXIT INT TERM

# ── Prerequisite checks ──────────────────────────────────────────────────────
log_step "1. Prerequisite checks"

if [[ ! -d "$MODEL_DIR" ]]; then
    log_error "Model directory not found at: $MODEL_DIR"
    log_error "Download it with: python scripts/download_model.py"
    exit 1
fi
log_info "✓ Model directory found"

if ! python -c "import mlx_lm" 2>/dev/null; then
    log_error "mlx_lm not installed."
    log_error "Run: pip install -r server/requirements.txt"
    exit 1
fi
log_info "✓ mlx_lm is installed"

if lsof -i :8001 -t >/dev/null 2>&1; then
    log_warn "Port 8001 is already in use.  Attempting to reuse existing server..."
else
    log_info "✓ Port 8001 is free"
fi

if lsof -i :5173 -t >/dev/null 2>&1; then
    log_warn "Port 5173 is already in use.  Frontend may fail to start."
fi

mkdir -p "$LOG_DIR"

# ── Start FastAPI Server (with MLX model loading) ────────────────────────────
log_step "2. Starting FastAPI server (MLX model loading, port 8001)"

cd "$SERVER_DIR"
python -m uvicorn app:app --host 0.0.0.0 --port 8001 \
    > "$LOG_DIR/server.log" 2>&1 &

SERVER_PID=$!
echo "$SERVER_PID" >> "$PIDS_FILE"
log_info "Server PID: $SERVER_PID (log: $LOG_DIR/server.log)"

# ── Wait for server to be ready (model loading takes ~10-30s) ────────────────
log_info "Waiting for MLX model to load and server to be ready..."
WAIT_MAX=120
WAIT_ELAPSED=0
while ! curl -s http://127.0.0.1:8001/health >/dev/null 2>&1; do
    sleep 3
    WAIT_ELAPSED=$((WAIT_ELAPSED + 3))
    if [[ $WAIT_ELAPSED -ge $WAIT_MAX ]]; then
        log_error "Server did not become ready within ${WAIT_MAX}s."
        log_error "Check logs: tail -f $LOG_DIR/server.log"
        exit 1
    fi
    printf "."
done
echo ""
log_info "✓ Server is ready (model loaded in ~${WAIT_ELAPSED}s)"

cd "$ROOT_DIR"

# ── Start Vue3 Frontend ──────────────────────────────────────────────────────
if $START_FRONTEND; then
    log_step "3. Starting Vue3 frontend (port 5173)"
    echo ""
    log_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log_info "  All services are running!"
    log_info ""
    log_info "  Frontend:  http://127.0.0.1:5173"
    log_info "  API:       http://127.0.0.1:8001"
    log_info "  Health:    http://127.0.0.1:8001/health"
    log_info "  API docs:  http://127.0.0.1:8001/docs"
    log_info ""
    log_info "  Press Ctrl+C to stop all services."
    log_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    cd "$ROOT_DIR/frontend"
    npx vite --host 127.0.0.1 --port 5173 2>&1
else
    log_step "3. Frontend skipped (--no-frontend)"
    log_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log_info "  Server running at http://127.0.0.1:8001"
    log_info "  Start frontend manually: cd frontend && npm run dev"
    log_info "  Press Ctrl+C to stop server."
    log_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    while true; do sleep 60; done
fi
