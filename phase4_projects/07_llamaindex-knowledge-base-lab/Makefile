# ============================================================
# P7: LlamaIndex 知识库应用 — Makefile
# 平台：macOS / Apple Silicon / Conda (cxllm)
# ============================================================

SHELL := /bin/bash
CONDA_BASE := $(shell conda info --base)
CONDA_ACTIVATE := source $(CONDA_BASE)/etc/profile.d/conda.sh && conda activate cxllm

export HF_ENDPOINT := https://hf-mirror.com

.PHONY: help setup download build query summary router test clean clean-all run-all

# ---- 默认目标 ----
help:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo " P7 LlamaIndex 知识库应用 — 命令列表"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@echo "  开发流程:"
	@echo "    make setup      — 一键初始化环境 + 安装依赖"
	@echo "    make download   — 下载 Embedding 模型 (BGE-Small-ZH)"
	@echo "    make build      — 构建 VectorStoreIndex 索引"
	@echo "    make query      — 启动交互式向量检索查询"
	@echo "    make summary    — 启动 SummaryIndex 全文总结查询"
	@echo "    make router     — 启动 RouterQueryEngine 多知识库路由"
	@echo "    make run-all    — 后台启动全部服务 (nohup)"
	@echo ""
	@echo "  测试 & 质量:"
	@echo "    make test       — 运行全部单元测试"
	@echo "    make test-verbose — 详细测试输出"
	@echo "    make lint       — 代码质量检查 (需要 ruff)"
	@echo ""
	@echo "  运维:"
	@echo "    make clean      — 清理缓存和构建产物"
	@echo "    make clean-all  — 深度清理 (包括模型文件)"
	@echo "    make status     — 查看运行状态 (进程 + 内存)"
	@echo "    make kill       — 停止所有后台 Python 进程"
	@echo "    make logs       — 实时查看应用日志"
	@echo ""

# ---- 环境初始化 ----
setup:
	@echo "🔧 初始化环境..."
	@$(CONDA_ACTIVATE) && \
		python --version && \
		pip install -U pip setuptools wheel -q && \
		pip install -r requirements.txt && \
		python -c "import torch; print('✅ MPS:', torch.backends.mps.is_available())"
	@echo "✅ 环境初始化完成"

# ---- 模型下载 ----
download:
	@echo "📥 下载 Embedding 模型..."
	@export HF_ENDPOINT=https://hf-mirror.com && \
		mkdir -p models && \
		hf download \
			BAAI/bge-small-zh-v1.5 \
			--local-dir models/bge-small-zh-v1.5
	@echo "✅ 模型下载完成"

# ---- 索引构建 ----
build:
	@echo "🔨 构建 VectorStoreIndex..."
	@$(CONDA_ACTIVATE) && python src/indexes/build_vector_index.py

build-summary:
	@echo "🔨 构建 SummaryIndex..."
	@$(CONDA_ACTIVATE) && python src/indexes/build_summary_index.py

# ---- 查询引擎 ----
query:
	@echo "🔍 启动 VectorStoreIndex 交互式查询..."
	@$(CONDA_ACTIVATE) && python src/query_engines/vector_query.py

summary:
	@echo "📝 启动 SummaryIndex 全文总结查询..."
	@$(CONDA_ACTIVATE) && python src/query_engines/summary_query.py

router:
	@echo "🧭 启动 RouterQueryEngine 多知识库路由..."
	@$(CONDA_ACTIVATE) && python src/routers/multi_kb_router.py

# ---- 一键启动全部服务（tmux 模式） ----
run-all-tmux:
	@echo "🚀 使用 tmux 启动全部服务..."
	@tmux new-session -d -s llamaindex -n build \
		"cd $(PWD) && $(CONDA_ACTIVATE) && echo '=== 构建索引 ===' && python src/indexes/build_vector_index.py; exec bash"
	@tmux new-window -t llamaindex -n query \
		"cd $(PWD) && $(CONDA_ACTIVATE) && sleep 3 && echo '=== 查询引擎 ===' && python src/query_engines/vector_query.py; exec bash"
	@tmux new-window -t llamaindex -n router \
		"cd $(PWD) && $(CONDA_ACTIVATE) && sleep 5 && echo '=== 路由器 ===' && python src/routers/multi_kb_router.py; exec bash"
	@tmux new-window -t llamaindex -n monitor \
		"cd $(PWD) && watch -n 3 'echo \"=== Memory ===\" && vm_stat | head -10 && echo && echo \"=== Python Processes ===\" && ps aux | grep python | grep -v grep || echo \"(none)\"'; exec bash"
	@echo ""
	@echo "✅ tmux 会话 'llamaindex' 已创建"
	@echo ""
	@echo "  连接：tmux attach -t llamaindex"
	@echo "  分屏：Ctrl+b % (垂直) / Ctrl+b \" (水平)"
	@echo "  切换：Ctrl+b o"
	@echo "  退出：Ctrl+b d (detach)"
	@echo "  终止：tmux kill-session -t llamaindex"

# ---- 一键启动全部服务（nohup 后台模式） ----
run-all:
	@echo "🚀 后台启动全部服务..."
	@mkdir -p logs
	@$(CONDA_ACTIVATE) && \
		nohup python src/indexes/build_vector_index.py \
			> logs/build.log 2>&1 & \
		echo "  build     PID $$! → logs/build.log"
	@sleep 10
	@$(CONDA_ACTIVATE) && \
		nohup python src/query_engines/vector_query.py \
			> logs/query.log 2>&1 & \
		echo "  query     PID $$! → logs/query.log"
	@echo ""
	@echo "✅ 服务已在后台启动"
	@echo "  查看日志: make logs"
	@echo "  查看状态: make status"
	@echo "  停止服务: make kill"

# ---- 测试 ----
test:
	@echo "🧪 运行单元测试..."
	@$(CONDA_ACTIVATE) && python -m pytest tests/ -v --tb=short

test-verbose:
	@echo "🧪 运行单元测试（详细模式）..."
	@$(CONDA_ACTIVATE) && python -m pytest tests/ -vv --tb=long

# ---- 代码质量 ----
lint:
	@echo "🔍 代码质量检查..."
	@$(CONDA_ACTIVATE) && ruff check src/ tests/ --fix || true
	@$(CONDA_ACTIVATE) && ruff format src/ tests/ --check || true

# ---- 运维命令 ----
status:
	@echo "📊 系统状态"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@echo "Python 进程:"
	@ps aux | grep python | grep -v grep || echo "  (无)"
	@echo ""
	@echo "统一内存:"
	@vm_stat | head -12
	@echo ""
	@echo "端口占用:"
	@lsof -i -P -n | grep python | head -10 || echo "  (无)"

logs:
	@echo "📋 实时日志 (Ctrl+C 退出)..."
	@tail -f logs/*.log 2>/dev/null || echo "  暂无日志文件，请先执行 make run-all"

kill:
	@echo "🛑 停止所有后台 Python 进程..."
	@pkill -f "src/indexes/" || true
	@pkill -f "src/query_engines/" || true
	@pkill -f "src/routers/" || true
	@sleep 1
	@echo "✅ 已停止"

# ---- 清理 ----
clean:
	@echo "🧹 清理缓存和构建产物..."
	@rm -rf storage/
	@rm -rf data/vector_store/*
	@rm -rf data/processed/*
	@rm -rf logs/*.log
	@rm -rf .pytest_cache/
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ 清理完成（模型文件已保留）"

clean-all: clean
	@echo "🧹 深度清理（包括模型文件）..."
	@rm -rf models/
	@echo "✅ 深度清理完成，下次需重新执行 make download"
