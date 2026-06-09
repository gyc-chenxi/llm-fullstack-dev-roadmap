# 🛠️ 11 — 开发工具链配置

> 🎯 **目标**：把 VS Code、终端、AI 编程助手配置到"即开即用"的工业级状态，让工具为效率服务。
> ⏱️ 预计时间：0.5 天

---

## 📋 为什么工具配置值得花半天？

| 对比 | 没配工具 | 配好工具 |
|------|---------|---------|
| 写代码 | 手动缩进、格式不统一 | ruff 自动格式化 |
| 调试 API | 反复手动写 curl | VS Code Thunder Client 一键 |
| 读大型 JSON | 文本编辑器打开卡死 | `jq` 命令行秒查 |
| 代码提示 | 等半天不出来 | AI 工具即时补全 |
| 环境切换 | `conda activate` 经常忘 | VS Code 自动识别 conda 环境 |

> 💡 工具投入 4 小时，未来 96 天每天省半小时 = 节省 48 小时。

---

## 1️⃣ VS Code 推荐插件

### 📌 必装（每天都会用到）

| 插件 | 用途 | 安装 |
|------|------|------|
| **Python** (ms-python.python) | Python 语法高亮/调试/环境选择 | VS Code 内搜索安装 |
| **Pylance** (ms-python.vscode-pylance) | 超强类型检查+自动补全 | 同上 |
| **Jupyter** (ms-toolsai.jupyter) | .ipynb 文件支持 | 同上 |
| **Ruff** (charliermarsh.ruff) | 实时代码检查+格式化 | 同上 |

### 📌 强烈推荐

| 插件 | 用途 |
|------|------|
| **Remote - SSH** (ms-vscode-remote.remote-ssh) | 远程连接服务器开发 |
| **Docker** (ms-azuretools.vscode-docker) | Dockerfile 语法 + 容器管理 |
| **GitLens** (eamodio.gitlens) | Git 可视化：看每行代码谁改的 |
| **GitHub Copilot** / **Continue** | AI 代码补全 |
| **Thunder Client** (rangav.vscode-thunder-client) | API 调试（Postman 轻量替代） |
| **Even Better TOML** (tamasfe.even-better-toml) | pyproject.toml 语法支持 |

### 📌 VS Code 关键设置

```json
// .vscode/settings.json（项目级 VS Code 配置）
{
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll.ruff": "explicit"
    }
  },
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.terminal.activateEnvironment": true,
  "files.exclude": {
    "**/__pycache__": true,
    "**/.pytest_cache": true,
    "**/.ipynb_checkpoints": true
  }
}
```

---

## 2️⃣ Jupyter 工作流

### 📌 Jupyter Lab vs VS Code Notebook

| 维度 | Jupyter Lab | VS Code Notebook |
|------|-----------|-----------------|
| 启动 | 浏览器打开 | VS Code 内直接开 |
| 变量查看 | 需要插件 | 自带变量浏览器 🔥 |
| 代码补全 | 一般 | Pylance 顶级 |
| Git 集成 | 麻烦 | 原生支持 |
| 远程连接 | 需 SSH 隧道 | Remote SSH 插件直连 |
| **Mac 推荐** | ⭐⭐ | ⭐⭐⭐⭐⭐ |

> 🔥 本项目的 notebook 全部在 VS Code 中打开。右键 .ipynb → "Open With" → "VS Code"。

### 📌 Jupyter Kernel 选 conda 环境

```bash
# 在 conda llm 环境中安装 ipykernel
conda activate llm
pip install ipykernel

# VS Code 打开 .ipynb → 右上角 Kernel 选择 → llm 环境
```

---

## 3️⃣ 终端美化（可选）

### 📌 Oh My Zsh

```bash
# 安装
sh -c "$(curl -fsSL https://raw.github.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"

# 推荐插件
# ~/.zshrc
plugins=(
  git              # git 快捷键（gst=git status, gco=git checkout...）
  zsh-autosuggestions  # 灰色自动建议（按 → 接受）
  zsh-syntax-highlighting  # 命令着色
)

# 安装插件
brew install zsh-autosuggestions zsh-syntax-highlighting
```

### 📌 Starship 提示符（轻量替代 Powerlevel10k）

```bash
# 安装
brew install starship

# 在 ~/.zshrc 末尾加
eval "$(starship init zsh)"
```

> 💡 Starship 比 Powerlevel10k 更轻量，默认外观就很舒服，不需要额外配置。

---

## 4️⃣ AI 编程工具的使用边界

### 📌 工具对比

| 工具 | 擅长 | 这个项目中用来做什么 |
|------|------|---------------------|
| **Claude Code** | 读整个项目、写多文件、修 Bug | 重构代码、写测试、生成文档 |
| **Cursor** | Tab 补全、Cmd+K 单文件编辑 | 日常快速编码 |
| **GitHub Copilot** | 行级补全 | 写样板代码、重复逻辑 |

### 📌 工程级 AI Prompt 写法

```
❌ 新手写法（AI 猜不到你要什么）：
"帮我写个函数"

✅ 工程级写法（AI 能精准输出）：
"在 phase3_rag/document_loader.py 中，
写一个 load_pdf() 函数：
- 输入：PDF 文件路径（str）
- 输出：list[dict] ，每条含 content + metadata（source, page）
- 用 pymupdf (fitz) 库
- 处理 FileNotFoundError，返回空列表
- 不超过 30 行代码"
```

### 📌 AI 使用红线

| ✅ 可以交给 AI | ❌ 不能交给 AI |
|---------------|---------------|
| 写重复性代码（CRUD、Schema） | 安全相关（鉴权、加密、限流逻辑） |
| 生成测试用例 | 核心业务逻辑决策 |
| 解释报错信息 | 不经审查直接 commit AI 代码 |
| 格式化代码 | 泄露 API Key / 密码到 AI 对话 |
| 写文档草稿 | 完全信任 AI 的"事实陈述" |

> ⚠️ **铁律**：AI 是超级实习生——又快又勤奋，但必须经过你的 Review 才能进生产。

---

## 5️⃣ API 调试工具

### 📌 curl

```bash
# 日常快速测试
curl -sS http://localhost:8000/healthz | python -m json.tool

# 测试聊天接口
curl -sS http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"你好"}],"max_tokens":256}' \
  | python -m json.tool --no-ensure-ascii
```

### 📌 httpie（curl 的友好替代）

```bash
brew install httpie

# 比 curl 更直观
http POST :8000/v1/chat/completions \
  messages:='[{"role":"user","content":"你好"}]' \
  max_tokens:=256
```

### 📌 VS Code Thunder Client（无需离开编辑器）

```
VS Code 左侧栏 → Thunder Client 图标 → New Request
→ 填 URL + Method + Body → Send
→ 响应自动 JSON 格式化，支持环境变量
```

---

## 6️⃣ JSON / YAML 处理技巧

### 📌 jq 命令行 JSON 处理

```bash
# 安装
brew install jq

# 美化输出
cat response.json | jq

# 提取字段
cat response.json | jq '.choices[0].message.content'

# 提取数组
cat response.json | jq '.choices[].message'

# 过滤
cat data.jsonl | jq 'select(.score > 0.8)'

# Python 管道结合
python -c "import json; print(json.dumps(data))" | jq
```

### 📌 Python json 模块进阶

```python
import json

# 美化输出（调试必备）
print(json.dumps(data, indent=2, ensure_ascii=False))

# 不要用 json.dumps 打印大型字典——
# 用 rich 库（pip install rich）
from rich import print as rprint
rprint(data)  # 自动语法着色 + 折叠

# 读 JSONL 文件
with open("data.jsonl") as f:
    records = [json.loads(line) for line in f if line.strip()]

# 写 JSONL（流式，不占内存）
with open("output.jsonl", "w") as f:
    for record in huge_iterator:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
```

### 📌 YAML 处理

```bash
# 命令行（需要安装 yq）
brew install yq
cat config.yaml | yq '.models[0].name'
```

```python
# Python 读 YAML 配置（Fallback 策略常用）
import yaml  # pip install pyyaml

with open("fallback_policy.yaml") as f:
    config = yaml.safe_load(f)
```

---

## 7️⃣ 数据库浏览工具

| 工具 | 平台 | 适用 |
|------|------|------|
| **VS Code SQLite Viewer** | VS Code 插件 | 快速看 .db / .sqlite3 文件 |
| **TablePlus** | macOS | 支持 PG/MySQL/Redis/SQLite |
| **pgcli** | 终端 | `pip install pgcli` → 自动补全 SQL |
| **Redis Insight** | macOS | Redis 官方 GUI |

---

## 🚨 翻车现场

| 现象 | 原因 | 解决 |
|------|------|------|
| VS Code 选了错误的 Python | 项目下有多个虚拟环境 | `Cmd+Shift+P` → "Python: Select Interpreter" |
| Jupyter kernel 连不上 | kernel 装了但 VS Code 不认识 | `pip install ipykernel` 在目标环境执行 |
| Copilot 代码有 bug | 完全信任 AI 输出 | 必须 Review！AI 生成的代码 bug 率不低 |
| ruff 没生效 | VS Code 没选 ruff 为 formatter | 检查 `.vscode/settings.json` 的 `editor.defaultFormatter` |
| `jq` 报 "parse error" | 输入不是合法 JSON | 先用 `cat` 确认输入格式，再看 `jq` 语法 |
| `python -m json.tool` 中文乱码 | 默认转义 | 加 `--no-ensure-ascii` |
| API Key 泄露到 AI 对话 | 粘贴代码时带了 Key | 🔴 用 `.env` + 环境变量，永远不硬编码 |

---

## ✅ 产出物 Checklist

- [ ] 安装 6 个必装 VS Code 插件（Python/Pylance/Jupyter/Ruff/Docker/GitLens）
- [ ] 配置 `.vscode/settings.json`（formatOnSave + ruff）
- [ ] 配置 Oh My Zsh + Starship（可选）
- [ ] 用 Thunder Client 发一个 POST 请求到本地 API
- [ ] 用 `jq` 解析一个 JSON 响应
- [ ] 学会写工程级 AI Prompt（给一个具体任务 + 约束条件）
- [ ] 配置好 VS Code 的 conda 环境选择
