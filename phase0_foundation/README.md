# Phase 0 🛠️ 工程师基建与极速复习

> **Day 1-5** | ⏱️ 5 天 | 📊 难度 ⭐

---

## 你将在本阶段学会什么

- ✅ 大模型开发最高频的 Python 特性（装饰器/async/Pydantic/NumPy/Pandas）
- ✅ ML/DL 核心概念复习（梯度下降/Softmax/过拟合/归一化）
- ✅ 神经网络架构全景（MLP/CNN/RNN/LSTM/GRU/GNN）
- ✅ NLP/CV/LLM 发展脉络 + 43 个核心概念术语表
- ✅ Git/GitHub/SSH 工作流 + Conventional Commits
- ✅ Docker + Redis + PostgreSQL 基础
- ✅ Linux/Shell 命令行 + PyTorch 基础
- ✅ 项目工程化脚手架 + 开发工具链配置

## 前置要求

- 有 Python 基础（会写函数、懂基本语法）
- 安装了 [conda](https://docs.conda.io/en/latest/miniconda.html) 或 [uv](https://docs.astral.sh/uv/)

## 学习天数与任务表

| Day | 主题 | 文件 | 产出 | ✅ |
|:---:|:-----|:-----|:-----|:--:|
| 1 | Python 高频特性 | `01_python_review.md` | 8 项能力 + NumPy/Pandas/Matplotlib | ☐ |
| 2 | ML/DL 基础 | `02_ml_dl_review.ipynb` | 梯度下降/Softmax/交叉熵/过拟合 | ☐ |
| 3 | 神经网络架构 | `03_neural_network_map.ipynb` | MLP/CNN/RNN/LSTM/GNN 代码实验 | ☐ |
| 4 | NLP/CV/LLM 全景 | `04_nlp_cv_llm_overview.ipynb` + `05_llm_concepts_glossary.md` | Tokenization/Embedding/ViT + 43 概念 | ☐ |
| 5 | 工程环境全栈 | `06-11` | Git/Docker/Linux/PyTorch/脚手架/工具链 | ☐ |

## 本阶段核心产出

- 🐍 一套完整的 Python 大模型开发技能
- 🐳 Docker Compose 一键启动 Redis + PostgreSQL
- 🔧 规范的项目脚手架（pyproject.toml + ruff + Makefile）
- 📓 3 个可直接运行的 Jupyter Notebook

## 如何运行本阶段 Demo

```bash
# Notebook
cd phase0_foundation
jupyter lab

# 打开 02_ml_dl_review.ipynb 或 03_neural_network_map.ipynb
# 按 Shift+Enter 逐 cell 运行
```

## 验收标准

- [ ] 能写出 `@retry` 装饰器
- [ ] 能用 `asyncio.gather` 并发请求
- [ ] 能用 Pydantic 定义数据模型
- [ ] 能从零 `git init` + `git push`
- [ ] 能用 Docker Compose 启动 Redis + PG

## 常见问题

| 问题 | 解决 |
|:-----|:-----|
| conda 下载慢 | 换清华源：`conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free/` |
| Docker Desktop 启动慢 | Mac 上正常现象，等 30s 即可 |
| Jupyter kernel 连不上 | `python -m ipykernel install --user --name llm-dev` |

## 面试可讲点

1. "我手写过 softmax 和梯度下降，理解数值稳定性"
2. "我知道为什么归一化参数不能用全数据集计算（防止数据泄漏）"
3. "我理解过拟合的本质和 6 种缓解方法"

## 下一阶段

👉 [Phase 1: Prompt、API 与商业网关雏形](../phase1_prompt_api/)
