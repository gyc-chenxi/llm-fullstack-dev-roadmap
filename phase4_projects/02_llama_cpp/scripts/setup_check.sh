#!/usr/bin/env bash
set -euo pipefail

# ──────────────────────────────────────────────────────────────────────────────
# setup_check.sh — validate that the environment is ready to run.
#
# Checks: conda env, Python deps, llama-server binary, model file, npm deps.
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
printf "${CYAN}  AI Gateway — Environment Readiness Check${NC}\n"
printf "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
echo ""

# ── Python environment ───────────────────────────────────────────────────────
echo "1. Python Environment"
check "conda is available"        command -v conda
check "conda env 'cxllm' exists"  bash -c "conda env list | grep -q cxllm"
check "fastapi installed"         bash -c "python -c 'import fastapi' 2>/dev/null"
check "httpx installed"           bash -c "python -c 'import httpx' 2>/dev/null"
check "pydantic installed"        bash -c "python -c 'import pydantic' 2>/dev/null"
echo ""

# ── llama.cpp ────────────────────────────────────────────────────────────────
echo "2. llama.cpp Inference Engine"
check "llama-server binary"       test -f "$ROOT_DIR/third_party/llama.cpp/build/bin/llama-server"
check "llama-gguf-split binary"   test -f "$ROOT_DIR/third_party/llama.cpp/build/bin/llama-gguf-split"
echo ""

# ── Model ────────────────────────────────────────────────────────────────────
echo "3. Model Weights"
check "Q4_K_M merged model"       test -f "$ROOT_DIR/models/qwen2.5-7b-instruct-q4_k_m.gguf"
echo ""

# ── Frontend ─────────────────────────────────────────────────────────────────
echo "4. Frontend (Vue3 + Vite)"
check "npm available"             command -v npm
check "node_modules installed"    test -d "$ROOT_DIR/frontend/vue3-sse-demo/node_modules"
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
    echo "  pip install fastapi uvicorn httpx pydantic pydantic-settings orjson pytest pytest-asyncio"
    echo "  ./scripts/build_llamacpp.sh          # compile llama.cpp"
    echo "  hf download Qwen/Qwen2.5-7B-Instruct-GGUF qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf --local-dir models"
    echo "  cd frontend/vue3-sse-demo && npm install"
else
    echo "All checks passed!  Start the stack:"
    echo ""
    echo "  make start"
    echo ""
    echo "Then open: http://127.0.0.1:5173"
fi
echo ""
