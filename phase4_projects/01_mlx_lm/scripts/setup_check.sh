#!/usr/bin/env bash
set -euo pipefail

# ──────────────────────────────────────────────────────────────────────────────
# setup_check.sh — validate that the MLX Chat environment is ready to run.
#
# Checks: conda env, mlx-lm, model dir, npm deps.
# Prints a friendly report and next-step instructions.
# ──────────────────────────────────────────────────────────────────────────────

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

PASS=0
FAIL=0

check() {
    local desc="$1"; shift
    if "$@" >/dev/null 2>&1; then
        printf "  ${GREEN}✓${NC} %s\n" "$desc"
        PASS=$((PASS + 1))
    else
        printf "  ${RED}✗${NC} %s\n" "$desc"
        FAIL=$((FAIL + 1))
    fi
}

echo ""
printf "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
printf "${CYAN}  MLX Local Chat — Environment Readiness Check${NC}\n"
printf "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
echo ""

# ── Python environment ───────────────────────────────────────────────────────
echo "1. Python Environment"
check "conda is available"        command -v conda
check "conda env 'cxllm' exists"  bash -c "conda env list | grep -q cxllm"
check "mlx-lm installed"          bash -c "python -c 'import mlx_lm' 2>/dev/null"
check "fastapi installed"         bash -c "python -c 'import fastapi' 2>/dev/null"
check "sqlmodel installed"        bash -c "python -c 'import sqlmodel' 2>/dev/null"
echo ""

# ── Model ────────────────────────────────────────────────────────────────────
echo "2. MLX Model"
check "Qwen2.5-7B-4bit model dir" test -d "$ROOT_DIR/models/Qwen2.5-7B-Instruct-4bit"
echo ""

# ── LoRA Adapter ─────────────────────────────────────────────────────────────
echo "3. LoRA Adapter"
check "identity_lora adapter"     test -d "$ROOT_DIR/adapters/identity_lora"
echo ""

# ── Frontend ─────────────────────────────────────────────────────────────────
echo "4. Frontend (Vue3 + Vite)"
check "npm available"             command -v npm
check "node_modules installed"    test -d "$ROOT_DIR/frontend/node_modules"
echo ""

# ── Summary ──────────────────────────────────────────────────────────────────
printf "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
printf "  Result: ${GREEN}${PASS} passed${NC}"
if [[ $FAIL -gt 0 ]]; then
    printf ", ${RED}${FAIL} failed${NC}"
fi
printf "\n"
printf "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
echo ""

if [[ $FAIL -gt 0 ]]; then
    echo "Fix the failed checks above, then re-run this script."
    echo ""
    echo "Quick fix commands:"
    echo "  conda create -n cxllm python=3.11    # if conda env missing"
    echo "  pip install -r server/requirements.txt"
    echo "  python scripts/download_model.py     # download MLX model (~8GB)"
    echo "  cd frontend && npm install"
else
    echo "All checks passed!  Start the stack:"
    echo ""
    echo "  make start"
    echo ""
    echo "Then open: http://127.0.0.1:5173"
fi
echo ""
