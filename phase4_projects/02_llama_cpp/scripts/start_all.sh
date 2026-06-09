#!/usr/bin/env bash
set -euo pipefail

# ──────────────────────────────────────────────────────────────────────────────
# start_all.sh — one-command launcher for the full AI Gateway stack.
#
# Usage:
#   ./scripts/start_all.sh              # Full stack (llama-server + gateway + frontend)
#   ./scripts/start_all.sh --no-frontend # AI services only, frontend you start manually
#
# What it does:
#   1. Validates prerequisites (model binary, llama-server, ports)
#   2. Starts llama-server in background → logs/llama-server.log
#   3. Waits for llama-server to be ready (poll /v1/models)
#   4. Starts FastAPI Gateway in background → logs/gateway.log
#   5. Starts Vue3 frontend in foreground (Ctrl+C stops everything)
#   6. On exit (Ctrl+C or error), cleans up all child processes
# ──────────────────────────────────────────────────────────────────────────────

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PIDS_FILE="$ROOT_DIR/.pids"
LOG_DIR="$ROOT_DIR/logs"
LLAMA_SERVER="${ROOT_DIR}/third_party/llama.cpp/build/bin/llama-server"
MODEL="${ROOT_DIR}/models/qwen2.5-7b-instruct-q4_k_m.gguf"

START_FRONTEND=true
if [[ "${1:-}" == "--no-frontend" ]]; then
    START_FRONTEND=false
fi

# ── Colour helpers ────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

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
    # Belt-and-suspenders: kill any remaining processes by name pattern.
    pkill -f "llama-server.*qwen2.5" 2>/dev/null || true
    pkill -f "uvicorn gateway.app" 2>/dev/null || true
    log_info "All services stopped.  Goodbye!"
}
trap cleanup EXIT INT TERM

# ── Prerequisite checks ──────────────────────────────────────────────────────
log_step "1. Prerequisite checks"

if [[ ! -f "$LLAMA_SERVER" ]]; then
    log_error "llama-server binary not found at: $LLAMA_SERVER"
    log_error "Run: ./scripts/build_llamacpp.sh"
    exit 1
fi
log_info "✓ llama-server binary found"

if [[ ! -f "$MODEL" ]]; then
    log_error "Model file not found at: $MODEL"
    log_error "Download it with: hf download Qwen/Qwen2.5-7B-Instruct-GGUF qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf --local-dir models"
    log_error "Then merge with: ./third_party/llama.cpp/build/bin/llama-gguf-split --merge models/qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf models/qwen2.5-7b-instruct-q4_k_m.gguf"
    exit 1
fi
log_info "✓ Model file found"

if lsof -i :8081 -t >/dev/null 2>&1; then
    log_warn "Port 8081 is already in use.  Attempting to reuse existing llama-server..."
else
    log_info "✓ Port 8081 is free"
fi

if lsof -i :8000 -t >/dev/null 2>&1; then
    log_warn "Port 8000 is already in use.  Gateway may fail to start."
fi

mkdir -p "$LOG_DIR"

# ── Start llama-server ───────────────────────────────────────────────────────
log_step "2. Starting llama-server (Metal / Q4_K_M / port 8081)"

"$LLAMA_SERVER" \
    -m "$MODEL" \
    --alias local-qwen2.5-7b-q4 \
    --host 127.0.0.1 \
    --port 8081 \
    -c 8192 \
    -b 512 \
    -ub 128 \
    -ngl 99 \
    --parallel 2 \
    --cache-prompt \
    --metrics \
    --log-timestamps \
    > "$LOG_DIR/llama-server.log" 2>&1 &

LLAMA_PID=$!
echo "$LLAMA_PID" >> "$PIDS_FILE"
log_info "llama-server PID: $LLAMA_PID (log: $LOG_DIR/llama-server.log)"

# ── Wait for llama-server to be ready ────────────────────────────────────────
log_info "Waiting for llama-server to be ready..."
WAIT_MAX=60
WAIT_ELAPSED=0
while ! curl -s http://127.0.0.1:8081/v1/models >/dev/null 2>&1; do
    sleep 2
    WAIT_ELAPSED=$((WAIT_ELAPSED + 2))
    if [[ $WAIT_ELAPSED -ge $WAIT_MAX ]]; then
        log_error "llama-server did not become ready within ${WAIT_MAX}s."
        log_error "Check logs: tail -f $LOG_DIR/llama-server.log"
        exit 1
    fi
    printf "."
done
echo ""
log_info "✓ llama-server is ready (took ~${WAIT_ELAPSED}s)"

# ── Start FastAPI Gateway ─────────────────────────────────────────────────────
log_step "3. Starting FastAPI Gateway (port 8000)"

uvicorn gateway.app:app --host 127.0.0.1 --port 8000 \
    > "$LOG_DIR/gateway.log" 2>&1 &

GATEWAY_PID=$!
echo "$GATEWAY_PID" >> "$PIDS_FILE"
log_info "Gateway PID: $GATEWAY_PID (log: $LOG_DIR/gateway.log)"

# Wait for Gateway to be ready.
sleep 3
if curl -s http://127.0.0.1:8000/healthz >/dev/null 2>&1; then
    log_info "✓ Gateway is ready"
else
    log_error "Gateway failed to start.  Check: tail -f $LOG_DIR/gateway.log"
    exit 1
fi

# ── Start Vue3 Frontend ──────────────────────────────────────────────────────
if $START_FRONTEND; then
    log_step "4. Starting Vue3 frontend (port 5173)"
    echo ""
    log_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log_info "  All services are running!"
    log_info ""
    log_info "  Frontend:  http://127.0.0.1:5173"
    log_info "  Gateway:   http://127.0.0.1:8000"
    log_info "  Health:    http://127.0.0.1:8000/healthz"
    log_info "  Metrics:   http://127.0.0.1:8000/gateway/metrics"
    log_info ""
    log_info "  Press Ctrl+C to stop all services."
    log_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    cd "$ROOT_DIR/frontend/vue3-sse-demo"
    npx vite --host 127.0.0.1 --port 5173 2>&1
else
    log_step "4. Frontend skipped (--no-frontend)"
    log_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log_info "  AI services running.  Start frontend manually:"
    log_info "    cd frontend/vue3-sse-demo && npm run dev"
    log_info "  Press Ctrl+C to stop AI services."
    log_info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    # Wait forever so Ctrl+C can trigger cleanup.
    while true; do sleep 60; done
fi
