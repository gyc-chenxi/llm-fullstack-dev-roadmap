#!/bin/bash
# SWE Agent 启动脚本
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$SCRIPT_DIR"

# 自动加载 .env 文件（如果有）
if [ -f "$SCRIPT_DIR/.env" ]; then
    set -a
    source "$SCRIPT_DIR/.env"
    set +a
fi

# 默认值
ISSUE="${1:-}"
REPO="${2:-}"
CONFIG="${3:-configs/agent_config.yaml}"

if [ -z "$ISSUE" ]; then
    echo "用法: $0 <issue描述> <仓库路径> [配置文件路径]"
    echo ""
    echo "示例:"
    echo '  ./scripts/run_agent.sh "divide(1,0) 返回 None 而非抛出异常" sample_repo'
    echo ""
    echo "内置 Issue 快捷用法:"
    echo "  ./scripts/run_agent.sh demo"
    exit 1
fi

# 内置 demo
if [ "$ISSUE" = "demo" ]; then
    ISSUE='函数 divide(a, b) 在 b 为 0 时返回 None，这是错误的。应该抛出 ZeroDivisionError("division by zero")。请修复这个 bug。'
    REPO="${REPO:-$SCRIPT_DIR/sample_repo}"
    echo "使用内置 demo Issue:"
    echo "$ISSUE"
    echo ""
fi

# 设置 API Key 提示
if [ -z "${OPENAI_API_KEY:-}" ] && [ -z "${ANTHROPIC_API_KEY:-}" ]; then
    echo "未检测到 API Key！"
    echo "   请先设置环境变量:"
    echo "   export OPENAI_API_KEY=sk-..."
    echo "   或"
    echo "   export ANTHROPIC_API_KEY=sk-ant-..."
    echo ""
    echo "   或者修改 configs/agent_config.yaml 中的 provider 和 model"
    exit 1
fi

echo "启动 SWE Agent..."
echo "  Issue: $ISSUE"
echo "  Repo:  $REPO"
echo "  Config: $CONFIG"
echo ""

python -m src.agent \
    --issue "$ISSUE" \
    --repo "$REPO" \
    --config "$CONFIG"