# 🖥️ 08 — Linux/Shell 命令行基础

> 🎯 **目标**：掌握大模型开发中最高频的 Shell 命令和脚本技能，能独立排查端口占用、查看日志、编写自动化脚本。
> ⏱️ 预计时间：1 天
> 🍎 默认环境：macOS + zsh（Apple Silicon）

---

## 📋 为什么大模型开发必须学命令行？

| 场景 | 不会命令行 | 会命令行 |
|------|----------|---------|
| 启动模型服务 | 找 GUI 按钮点半天 | `./start_all.sh` 一键启动 |
| 排查端口冲突 | "为什么 8081 启动不了？" | `lsof -i :8081` 秒定位 |
| 查看日志 | 打开几百 MB 的日志文件 | `tail -f gateway.log | grep ERROR` |
| SSH 连服务器 | 不会连 | `ssh myserver` 免密直连 |
| Docker 操作 | Docker Desktop 点来点去 | `docker compose up -d` 一行搞定 |
| 批量处理文件 | 手动一个个改 | `for f in *.json; do ... done` |

> 💡 大模型工程师 80% 的日常操作在终端完成。不需要成为 Linux 专家，这 20 个命令能覆盖绝大多数场景。

---

## 1️⃣ macOS 终端基础

### 📌 推荐终端

| 终端 | 特点 | 安装 |
|------|------|------|
| **iTerm2** | 分屏/热键/颜色丰富 | `brew install --cask iterm2` |
| **Warp** | AI 集成/GUI 辅助 | `brew install --cask warp` |
| **VS Code Terminal** | 开发时最方便 | VS Code 内置 `Ctrl+`` |

### 📌 zsh 基础配置

```bash
# 查看当前 shell
echo $SHELL          # → /bin/zsh（macOS 默认）

# zsh 配置文件
~/.zshrc             # 每次打开终端执行
~/.zprofile          # 登录时执行一次

# 修改后立即生效
source ~/.zshrc
```

---

## 2️⃣ 文件系统导航

```bash
# 基础导航（每个字母都天天用）
pwd                  # 📍 我在哪？ → /Users/chenxi/Documents
ls                   # 📋 列出当前目录
ls -la               # 📋  详细信息（含隐藏文件、权限）
ls -lh               # 📋  人类可读的文件大小
cd /path/to/dir      # 📂 进入目录
cd ..                # 📂 返回上一级
cd -                 # 📂 回到刚才的目录
cd ~                 # 🏠 回家目录

# 目录操作
mkdir my_project     # 📁 创建目录
mkdir -p a/b/c       # 📁 递归创建（中间目录自动建）
rm file.txt          # 🗑️ 删除文件
rm -rf dir/          # ☠️ 递归强制删除（危险！没有回收站！）
cp source dest       # 📄 复制
cp -r src/ dest/     # 📁 复制目录
mv old new           # ✏️ 移动/重命名

# 查找
find . -name "*.py"              # 🔍 按文件名搜索
find . -name "*.py" -not -path "*/__pycache__/*"  # 排除目录
find . -type f -name "*.log" -mtime -7            # 最近7天修改的日志
```

---

## 3️⃣ 文件查看与搜索

```bash
# 查看文件
cat file.txt          # 📖 打印全部（小文件）
head -20 file.txt     # 📖 前 20 行
tail -20 file.txt     # 📖 后 20 行
tail -f app.log       # 🔄 实时追踪日志（调试必备！）
less file.txt         # 📖 分页浏览（大文件推荐，q 退出）

# 搜索利器 grep
grep "ERROR" app.log                    # 🔎 找含 ERROR 的行
grep -i "error" app.log                 # 🔎 忽略大小写
grep -r "def main" ./src               # 🔎 递归搜索目录
grep -n "TODO" *.py                     # 🔎 显示行号
grep -v "DEBUG" app.log                 # 🔎 排除含 DEBUG 的行
grep "ERROR\|FATAL" app.log             # 🔎 匹配多个模式
ps aux | grep python                    # 🔎 查找 Python 进程

# 统计
wc -l file.txt         # 📏 行数
wc -w file.txt         # 📏 单词数
du -sh ./models/       # 📏 目录大小（-h 人类可读）
df -h                  # 📏 磁盘使用情况
```

---

## 4️⃣ 管道与重定向

```bash
# 管道 | ：把左边命令的输出传给右边命令
ls -la | grep ".py"                  # 列出 → 过滤 .py 文件
cat access.log | grep "404" | wc -l # 统计 404 数量
ps aux | grep python | awk '{print $2}' | xargs kill  # 杀所有 Python 进程

# 重定向
echo "hello" > file.txt      # → 覆盖写入
echo "world" >> file.txt     # → 追加写入
python app.py > out.log 2>&1 # → 标准输出+错误都写日志
python app.py > /dev/null 2>&1  # → 丢弃所有输出

# stdin/stdout/stderr 速记
# 0 = stdin（标准输入）
# 1 = stdout（标准输出）
# 2 = stderr（标准错误）
# 2>&1 = 把 stderr 重定向到 stdout
```

---

## 5️⃣ 权限基础

```bash
# 查看权限
ls -la
# -rw-r--r--  1 chenxi  staff  1024 Jun 8 10:00 file.txt
#  ↑  ↑  ↑
#  user group others

# 权限符号：r=读(4) w=写(2) x=执行(1)

# 修改权限
chmod +x script.sh            # ➕ 加执行权限
chmod 755 script.sh           # 🔐 自己全权限，别人读+执行
chmod 600 ~/.ssh/id_ed25519   # 🔐 只有自己能读写（SSH 密钥必须！）
chmod -R 755 ./project/       # 📁 递归设置

# 修改所有者
chown user:group file
```

> ⚠️ 绝对不要 `chmod 777`！等于给全世界你的文件权限。

---

## 6️⃣ 进程管理

```bash
# 查看进程
ps aux                     # 📋 所有进程
ps aux | grep python       # 🔎 找 Python 进程
top                        # 🔄 实时进程监控（CPU/内存）
htop                       # 🔄 更好看的 top（brew install htop）

# 端口相关（高频！）
lsof -i :8081              # 🔍 谁占了 8081 端口？
lsof -i :8081 | grep LISTEN | awk '{print $2}' | xargs kill  # 杀掉占端口的进程

# 进程控制
kill <PID>                 # 🛑 正常终止
kill -9 <PID>              # ☠️ 强制杀死
killall -9 python          # ☠️ 杀所有 Python 进程（谨慎！）

# 后台运行
python app.py &             # 后台运行
Ctrl-Z                     # 暂停当前前台进程
bg                         # 恢复为后台
fg                         # 拉回前台
nohup python app.py &      # 关终端也不停
```

### 📌 macOS 特殊问题：AirPlay 占端口

```bash
# macOS 的 AirPlay Receiver 默认占用端口 5000
# 如果你的服务需要 5000 端口：
# 系统设置 → 通用 → AirDrop 与 Handoff → 关闭 AirPlay Receiver
# 或者直接用 8000/8081 等其他端口
```

---

## 7️⃣ 环境变量

```bash
# 查看
echo $PATH               # 📍 可执行文件搜索路径
echo $HOME               # 🏠 家目录
printenv                 # 📋 所有环境变量

# 临时设置（仅当前 shell）
export MY_VAR="hello"
echo $MY_VAR             # → hello

# 永久设置：写入 ~/.zshrc
echo 'export HF_ENDPOINT=https://hf-mirror.com' >> ~/.zshrc
source ~/.zshrc

# 常用环境变量（大模型开发）
export CUDA_VISIBLE_DEVICES=0          # 指定 GPU
export HF_HOME=/path/to/models         # HuggingFace 缓存目录
export PYTHONPATH=/path/to/project     # Python 模块搜索路径
```

---

## 8️⃣ Shell 脚本基础

```bash
#!/bin/bash
# shebang — 告诉系统用哪个解释器执行

# 变量
PROJECT_NAME="llm-gateway"
PORT=8000
echo "启动 $PROJECT_NAME，端口 $PORT"

# 条件
if [ -f ".env" ]; then
    echo "✅ .env 文件存在"
else
    echo "❌ 缺少 .env 文件，复制 .env.example"
    cp .env.example .env
fi

# 循环
for model in qwen llama deepseek; do
    echo "下载 $model 模型..."
done

# 函数
cleanup() {
    echo "🧹 清理..."
    kill $SERVER_PID 2>/dev/null
}

# 🔑 trap：脚本退出时自动清理
trap cleanup EXIT

# 参数
echo "第一个参数: $1"
echo "所有参数: $@"
echo "参数个数: $#"
```

### 📌 实战：模型下载 + 启动脚本

```bash
#!/bin/bash
set -e  # 任何命令失败就退出

MODEL_DIR="./models"
PORT=8081

echo "🔄 检查模型文件..."
if [ ! -f "$MODEL_DIR/qwen2.5-7b-q4_k_m.gguf" ]; then
    echo "📥 下载模型..."
    hf download Qwen/Qwen2.5-7B-Instruct-GGUF \
      qwen2.5-7b-instruct-q4_k_m.gguf \
      --local-dir "$MODEL_DIR"
fi

echo "🚀 启动 llama-server (端口 $PORT)..."
llama-server \
  -m "$MODEL_DIR/qwen2.5-7b-q4_k_m.gguf" \
  --port "$PORT" \
  -ngl 99 &

sleep 3

echo "✅ 模型服务已启动: http://localhost:$PORT"
echo "📍 测试: curl http://localhost:$PORT/health"
```

---

## 9️⃣ 常用工具

```bash
# curl — API 调试必备
curl http://localhost:8000/healthz                     # GET
curl -X POST http://localhost:8000/v1/chat/completions \  # POST + JSON
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"你好"}]}'
curl -sS http://localhost:8000/healthz | python -m json.tool  # 格式化 JSON 输出

# 压缩解压
tar -czf archive.tar.gz ./project/    # 📦 打包+压缩
tar -xzf archive.tar.gz               # 📦 解压
unzip file.zip                         # 📦 解压 zip

# ssh/scp — 远程操作
ssh user@server                       # 远程登录
ssh -i ~/.ssh/mykey user@server       # 指定密钥登录
scp file.txt user@server:~/           # 上传文件
scp -r ./dir user@server:~/           # 上传目录
```

---

## 🔟 大模型开发最常用 20 个命令速查表

| # | 命令 | 使用频率 | 场景 |
|---|------|---------|------|
| 1 | `ls -la` | 每天 50 次 | 看文件 |
| 2 | `cd` / `cd ..` | 每天 100 次 | 切目录 |
| 3 | `pwd` | 每天 5 次 | 确认位置 |
| 4 | `conda activate llm` | 每次开终端 | 激活环境 |
| 5 | `python app.py` | 每天 10 次 | 启动服务 |
| 6 | `tail -f logs/app.log` | 调试时 | 看日志 |
| 7 | `grep "ERROR" *.log` | 排错时 | 搜错误 |
| 8 | `lsof -i :端口` | 端口冲突时 | 查端口 |
| 9 | `kill -9 <PID>` | 偶尔 | 杀进程 |
| 10 | `ps aux \| grep python` | 偶尔 | 找进程 |
| 11 | `docker compose up -d` | 每天 2 次 | 启动服务 |
| 12 | `docker compose logs -f` | 调试时 | 容器日志 |
| 13 | `curl localhost:8000/healthz` | 每天 10 次 | API 测试 |
| 14 | `git status / add / commit / push` | 每天 20 次 | 版本管理 |
| 15 | `source ~/.zshrc` | 改配置后 | 重载配置 |
| 16 | `find . -name "*.py"` | 偶尔 | 找文件 |
| 17 | `du -sh ./models/` | 偶尔 | 看大小 |
| 18 | `wc -l data.jsonl` | 偶尔 | 数行数 |
| 19 | `chmod +x script.sh` | 新建脚本时 | 加权限 |
| 20 | `Ctrl-C` | 每天 20 次 | 停止程序 |

---

## 🚨 翻车现场

| 现象 | 原因 | 解决 |
|------|------|------|
| `command not found` | 没装这个工具 / PATH 没配 | `brew install xxx` 或 `which xxx` 检查 |
| `rm -rf /` 误删 | 打错路径 | 用 `trash` 命令替代（`brew install trash`） |
| `port already in use` | 端口被占用 | `lsof -i :端口` 找到并 kill |
| `permission denied` | 没执行权限 | `chmod +x file.sh` |
| `conda: command not found` | conda 未初始化 | `conda init zsh` → 重启终端 |
| `No such file or directory` | 路径错误/大小写 | macOS 默认不区分，但 Linux 区分！ |
| `zsh: no matches found` | 通配符没匹配到文件 | 加引号或 `setopt nonomatch` |
| 脚本执行完进程也停了 | 没放后台 | 加 `&` 或 `nohup` |
| `brew install` 报错 | Homebrew 版本老 | `brew update` 后重试 |

---

## ✅ 产出物 Checklist

- [ ] 安装 iTerm2 或配置好 VS Code Terminal
- [ ] 在终端完成一次"创建目录 → 写脚本 → chmod → 运行 → kill 进程"全流程
- [ ] 用 `tail -f` 追踪一个日志文件，同时 `grep` 过滤
- [ ] 写一个带 `trap cleanup EXIT` 的启动脚本
- [ ] 用 `lsof -i` 排查一次端口冲突
- [ ] 配置好 `~/.zshrc`（至少加上 HuggingFace 镜像和 conda init）
- [ ] 用 `ps aux | grep` + `kill` 杀掉一个卡死的进程
