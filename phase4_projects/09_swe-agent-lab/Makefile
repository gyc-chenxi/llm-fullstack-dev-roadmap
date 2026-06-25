# ============================================================
# mini-swe-agent Makefile
# 使用: make <target>
# ============================================================

.PHONY: help setup install init-repo run-demo run-agent test test-quick clean clean-all

help: ## 显示帮助
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## 一键初始化：安装依赖 + 初始化 sample repo
	$(MAKE) install
	$(MAKE) init-repo
	@echo "环境就绪！运行 'make run-demo' 启动 Agent"

install: ## 安装 Python 依赖
	pip install -e ".[dev]"
	pip install -r requirements.txt

init-repo: ## 初始化 sample_repo 为 git 仓库
	@bash scripts/setup_sample_repo.sh

run-demo: ## 使用内置 demo Issue 运行 Agent（自动重置 sample_repo）
	@cd sample_repo && git checkout -- . 2>/dev/null || true
	@echo "sample_repo 已重置到干净状态"
	@bash scripts/run_agent.sh demo

run-agent: ## 运行自定义 Agent：make run-agent ISSUE="..." REPO="..."
	@bash scripts/run_agent.sh "$(ISSUE)" "$(REPO)" "$(CONFIG)"

test: ## 运行所有测试
	python -m pytest tests/ -v --tb=short --cov=src --cov-report=term-missing

test-quick: ## 快速运行测试（不测 coverage）
	python -m pytest tests/ -v --tb=short -q

clean: ## 清理缓存和生成物
	rm -rf build/ dist/ *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete
	rm -rf .pytest_cache .coverage htmlcov/
	@echo "已清理"

clean-all: clean ## 深度清理（包括 sample_repo 的 git 仓库）
	rm -rf sample_repo/.git
	@echo "已深度清理（sample_repo 的 .git 已删除）"