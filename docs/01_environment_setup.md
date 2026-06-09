# 环境搭建完整指南

> 从头搭建大模型开发的完整本地环境

---

## 硬件要求

| 配置 | 最低 | 推荐 |
|------|------|------|
| 内存 | 16GB | 32GB+ 统一内存 (Apple Silicon) |
| 硬盘 | 50GB 空闲 | 100GB+ 空闲（模型文件很大） |
| GPU | 无（CPU 推理） | Apple M 系列 / NVIDIA 8GB+ VRAM |
| 系统 | macOS 14+ / Ubuntu 22.04+ / Windows WSL2 |

## Step 1：安装 Conda

```bash
# macOS
brew install miniconda

# 初始化
conda init zsh
# 重启终端
```

## Step 2：创建虚拟环境

```bash
conda create -n llm python=3.11
conda activate llm
```

## Step 3：安装基础依赖

```bash
pip install -r requirements.txt
```

## Step 4：安装 Docker（可选但推荐）

```bash
# macOS
brew install --cask docker

# 验证
docker run hello-world
```

## Step 5：配置 Git 和 SSH

```bash
git config --global user.name "你的名字"
git config --global user.email "你的邮箱"

# 生成 SSH 密钥
ssh-keygen -t ed25519 -C "你的邮箱"
cat ~/.ssh/id_ed25519.pub
# 复制到 GitHub Settings → SSH Keys
```

## Step 6：安装 Node.js（前端 Demo 需要）

```bash
# macOS
brew install node@18
```

## 验证环境

```bash
# 确认 Python
python --version  # 应该输出 Python 3.11.x

# 确认 conda 环境
conda info --envs  # 应该看到 llm 环境

# 确认 PyTorch
python -c "import torch; print(torch.__version__)"

# 确认 FastAPI
python -c "import fastapi; print(fastapi.__version__)"

# 确认 Docker
docker --version
```

---

> 遇到问题请参考 `docs/05_troubleshooting.md`
