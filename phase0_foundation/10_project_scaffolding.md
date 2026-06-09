# 📦 10 — 项目工程化脚手架

> 🎯 **目标**：学会从零搭建一个 Python 项目，理解 pyproject.toml、虚拟环境、.env、pre-commit 的配置。
> ⏱️ 预计时间：0.5 天

---

## 📋 为什么要学"项目工程化"？

| 场景 | 没有工程化 | 有工程化 |
|------|---------|---------|
| 换台电脑 | "我环境怎么配来着？" | `uv sync` 一键重建 |
| 协作开发 | 10 个人 10 种代码风格 | pre-commit 自动格式统一 |
| 部署上线 | 依赖冲突，线上炸了 | 依赖锁定，线上和本地一致 |
| .env 泄露 | API Key 传到 GitHub | .gitignore + .env.example 防护 |
| 代码质量 | 手动改格式，浪费时间 | ruff 自动格式化 + 检查 |

> 💡 工程化的本质：**减少重复劳动，防止低级错误**。

---

## 1️⃣ 项目目录结构规范

### 📌 两种主流结构

```
# Flat layout（简单项目推荐 🔥）
my-project/
├── app.py                  # 主入口
├── config.py               # 配置
├── routes/                 # 路由
├── models/                 # 数据模型
├── tests/                  # 测试
├── pyproject.toml
├── .env.example
└── README.md

# src layout（大型项目/要发布到 PyPI 的包）
my-project/
├── src/
│   └── mypkg/
│       ├── __init__.py
│       ├── app.py
│       └── ...
├── tests/
├── pyproject.toml
└── README.md
```

> 本项目（100 天路线）使用 **Flat Layout**。src layout 多一层嵌套，对学习阶段反而碍事。

### 📌 本项目各 Phase 的目录结构示例

```
phase3_rag/          # Flat layout 示例
├── app.py              # FastAPI 主入口
├── config.py           # pydantic-settings
├── schemas.py          # 请求/响应模型
├── document_loader.py  # 文档解析模块
├── vector_store.py     # 向量存储模块
├── requirements.txt    # 传统依赖（如有）
├── pyproject.toml      # 现代项目配置
├── .env.example        # 环境变量模板
└── README.md           # 项目说明
```

---

## 2️⃣ 项目配置：pyproject.toml

```
Python 项目配置演进：
  setup.py (2004-)  →  requirements.txt (2008-)  →  pyproject.toml (2021-)
  "啥都能写"              "只列依赖"                 "现代化标准，包配置+依赖+工具统一"
```

### 📌 基础 pyproject.toml 模板

```toml
[project]
name = "phase3-rag"
version = "0.1.0"
description = "RAG 检索增强生成学习项目"
requires-python = ">=3.10,<3.12"
dependencies = [
    "fastapi>=0.110.0",
    "uvicorn[standard]>=0.29.0",
    "pydantic>=2.7.0",
    "pydantic-settings>=2.3.0",
    "httpx>=0.27.0",
    "openai>=1.30.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "ruff>=0.3.0",
]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W"]  # pyflakes + isort + pep8-naming

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

### 📌 pyproject.toml vs requirements.txt

| 维度 | pyproject.toml | requirements.txt |
|------|---------------|-----------------|
| 用途 | 包发布 + 依赖 + 工具配置 | 纯依赖列表 |
| 格式 | TOML（结构化） | 纯文本 |
| 锁版本 | ❌ 不锁（配合 lockfile） | 可选 `==1.2.3` 锁死 |
| 多组依赖 | ✅ `[optional-dependencies]` | ❌ 需多个文件 |
| 工具配置 | ✅ ruff/pytest/mypy 统一管理 | ❌ 需各自配置文件 |
| 推荐度 | ⭐⭐⭐⭐⭐ 现代首选 | ⭐⭐⭐ 简单场景 |

> 🔥 本项目建议：**小型脚本用 requirements.txt，中型项目用 pyproject.toml**。

---

## 3️⃣ 虚拟环境深度讲解

### 📌 三种方案对比

| 方案 | 速度 | 隔离性 | 依赖锁定 | 适用 |
|------|------|--------|---------|------|
| **conda** | 慢（首次） | 强（含 C 库） | `environment.yml` | 科学计算/Mac 主力 |
| **venv** | 快 | 中（仅 Python 包） | `requirements.txt` | 轻量项目 |
| **uv** | 🔥 极快（10-100x） | 中 | `uv.lock` → 确定性锁定 | 速度追求者 |

### 📌 conda 工作流

```bash
# 创建环境
conda create -n llm python=3.11
conda activate llm

# 安装依赖
pip install -r requirements.txt

# 导出环境（给他人复现）⚠️ 跨平台可能有问题
conda env export > environment.yml

# 🚫 常见伪交叉平台问题：conda 导出的 environment.yml 包含 macOS 特有的包
# 他人用 Linux 装了会报错
# ✅ 正确做法：environment.yml 只写关键包 + 配合 pip requirements.txt
```

### 📌 venv 工作流

```bash
# 创建
python3 -m venv .venv
source .venv/bin/activate

# 安装
pip install -r requirements.txt

# 退出
deactivate

# 🔑 .venv/ 必须在 .gitignore 中！
```

### 📌 uv 工作流（推荐 🔥）

```bash
# 安装 uv
brew install uv  # macOS
# 或 curl -LsSf https://astral.sh/uv/install.sh | sh

# 创建环境 + 安装依赖（一行！）
uv sync                  # 读取 pyproject.toml，自动创建 .venv + 安装

# 安装单个包
uv pip install fastapi

# 锁定依赖（生成 uv.lock）
uv lock

# 导出 requirements.txt
uv pip freeze > requirements.txt

# 🚀 速度对比
# pip install torch → 2 分钟
# uv pip install torch → 15 秒（缓存后更 快）
```

### 📌 选型建议

```
你是 Mac 做 LLM 开发：
  → conda 创建环境（管理 Python 版本 + C 库）
  → uv pip install 装包（快 10-100 倍）
  → requirements.txt 作为依赖列表
```

---

## 4️⃣ .env 与环境变量管理

### 📌 .env 文件格式

```bash
# .env（⚠️ 这个文件绝对不能进 Git！）
OPENAI_API_KEY=sk-proj-abc123
DEEPSEEK_API_KEY=sk-xyz789
GATEWAY_API_KEY=my-secret-key

# 数据库
POSTGRES_USER=llm
POSTGRES_PASSWORD=change_me_in_production
```

### 📌 .env.example 模板

```bash
# .env.example（✅ 这个可以进 Git，作为模板）
OPENAI_API_KEY=sk-your-key-here
DEEPSEEK_API_KEY=sk-your-key-here
GATEWAY_API_KEY=change-me

# 数据库（本地开发默认值）
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=llm
POSTGRES_PASSWORD=change_me
```

### 📌 python-dotenv 使用

```python
# config.py
import os
from dotenv import load_dotenv

load_dotenv()  # 自动读取 .env 文件

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("请在 .env 中设置 OPENAI_API_KEY")

# pydantic-settings 方式（更推荐 🔥）
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    gateway_api_key: str = "dev-key"

    model_config = {"env_file": ".env"}

settings = Settings()
```

### 📌 .gitignore 配置

```gitignore
# 环境变量文件（绝对不能进 Git！）
.env
.env.local
.env.production

# 保留模板文件
!.env.example

# IDE
.vscode/
.idea/

# Python
__pycache__/
*.pyc
.venv/
venv/

# 虚拟环境
*.egg-info/

# 模型文件
*.gguf / *.bin / *.pt / *.safetensors
```

---

## 5️⃣ pre-commit + ruff 代码格式化

### 📌 pre-commit 配置

```bash
# 安装
pip install pre-commit ruff
# 或：uv pip install pre-commit ruff

# 初始化
pre-commit install  # 之后每次 git commit 会自动检查
```

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.3.0
    hooks:
      - id: ruff              # 代码检查（替代 flake8）
        args: [--fix]
      - id: ruff-format       # 代码格式化（替代 black）
```

### 📌 ruff 效果演示

```python
# ruff format 之前：
import os,sys
def foo (x,y):
    result=x+y
    return result

# ruff format 之后：
import os
import sys


def foo(x, y):
    result = x + y
    return result
```

> 💡 ruff 的优势：Rust 编写，比 flake8+black+isort 加起来快 100 倍以上。

---

## 6️⃣ Makefile 常用任务

```makefile
.PHONY: install run test lint clean

# 安装依赖
install:
	conda activate llm && uv pip install -r requirements.txt

# 启动服务
run:
	python app.py

# 运行测试
test:
	pytest -v

# 代码检查
lint:
	ruff check . && ruff format --check .

# 格式化代码
format:
	ruff check --fix . && ruff format .

# 清理
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
```

---

## 🚨 翻车现场

| 现象 | 原因 | 解决 |
|------|------|------|
| `.env` 推到 GitHub 了 | 忘了加到 .gitignore | **立即改所有 API Key** + `git rm --cached .env` + 加 .gitignore |
| `conda install` 和 `pip install` 混用 | 依赖冲突 | conda 只建环境，装包全用 pip |
| `ModuleNotFoundError` | import 路径不对 | 检查 `PYTHONPATH` 或目录结构 |
| ruff 和 black 冲突 | 两个格式化工具打架 | 只用 ruff（自带 formatter） |
| `uv sync` 后环境是空的 | 没配 pyproject.toml | 确认 `[project]` 下有 `dependencies` |
| pre-commit hook 报错 | hook 版本不对 | `pre-commit autoupdate` 更新到最新 |

---

## ✅ 产出物 Checklist

- [ ] 建一个项目：`mkdir my-llm-project && cd my-llm-project`
- [ ] 编写 `pyproject.toml`（含依赖 + ruff 配置）
- [ ] 创建 `.env.example` 和 `.gitignore`
- [ ] 用 `uv sync` 一键安装依赖
- [ ] 配置 pre-commit + ruff
- [ ] 写 `Makefile`（至少 install/run/test/lint 四个 target）
- [ ] 把所有内容 `git init` + `git add` + 提交
- [ ] 验证 `.env` 不会出现在 git status 中
