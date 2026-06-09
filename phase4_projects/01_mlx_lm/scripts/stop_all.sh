#!/usr/bin/env bash
set -euo pipefail

# ──────────────────────────────────────────────────────────────────────────────
# stop_all.sh — graceful shutdown of all MLX Chat services.
# ──────────────────────────────────────────────────────────────────────────────

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PIDS_FILE="$ROOT_DIR/.pids"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

log_info() { printf "${GREEN}[INFO]${NC}  %s\n" "$*"; }
log_warn() { printf "${RED}[WARN]${NC}  %s\n" "$*"; }

STOPPED=0

# 1. Try PID file.
if [[ -f "$PIDS_FILE" ]]; then
    while read -r pid; do
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
            log_info "Stopped PID $pid"
            STOPPED=$((STOPPED + 1))
        fi
    done < "$PIDS_FILE"
    rm -f "$PIDS_FILE"
else
    log_warn "No .pids file found — falling back to pkill."
fi

# 2. Belt-and-suspenders: kill by process name pattern.
pkill -f "uvicorn.*server.app" 2>/dev/null && {
    log_info "Stopped running server processes"; STOPPED=$((STOPPED + 1));
} || true

pkill -f "vite.*5173" 2>/dev/null && {
    log_info "Stopped running vite processes"; STOPPED=$((STOPPED + 1));
} || true

if [[ $STOPPED -eq 0 ]]; then
    log_warn "No running services found."
else
    log_info "Done.  All services stopped."
fi
