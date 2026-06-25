#!/bin/bash
# 初始化 sample_repo 为 git 仓库（Agent 的 git_diff 工具需要）
set -e

SAMPLE_DIR="$(cd "$(dirname "$0")/../sample_repo" && pwd)"

echo "初始化 sample_repo git 仓库..."

cd "$SAMPLE_DIR"

# 初始化 git
git init -q
git config user.email "demo@example.com"
git config user.name "Demo User"

# 首次提交（带 bug 的版本）
git add calculator.py test_calculator.py
git commit -qm "feat: 初始计算器实现（含已知 bug）"

echo "sample_repo 已初始化为 git 仓库"
echo "$SAMPLE_DIR"
echo ""
echo "当前已知 bug:"
echo "  1. divide(1, 0) 返回 None 而非抛出 ZeroDivisionError"
echo ""
echo "运行以下命令确认测试失败:"
echo "  cd $SAMPLE_DIR && python -m pytest test_calculator.py -v"