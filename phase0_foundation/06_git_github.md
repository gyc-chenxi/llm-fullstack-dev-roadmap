# 🔧 06 — Git、GitHub 与 SSH

> 🎯 **目标**：建立规范的代码版本管理习惯，把仓库推上 GitHub，配置好免密 SSH。
> ⏱️ 预计时间：0.5 天

---

## 📋 为什么第一步就要学 Git？

| 场景 | 不会 Git | 会 Git |
|------|---------|--------|
| 代码改坏了 | 手动备份 → `代码_v1.py` `代码_v2_最终.py` | `git checkout` 秒回退 |
| 想尝试新功能 | 复制整个项目文件夹 | `git branch` 开分支，不行就删 |
| 跟同学协作 | 微信发代码压缩包 | PR + Review 专业协作 |
| 投简历 | "会用 Git" | GitHub 绿点墙证明你真的在用 |

---

## 1️⃣ Git 核心概念（5 分钟速通）

```
工作区                    暂存区                 本地仓库              远程仓库
(你的文件)  ──git add──→  (staging)  ──git commit──→  (.git)  ──git push──→  (GitHub)
   ↑                                                        ↓
   └──────────────── git pull / git checkout ────────────────┘
```

| 概念 | 一句话 | 类比 |
|------|--------|------|
| **repo** | 代码 + 所有历史版本 | 一个项目的"时光机" |
| **commit** | 一次保存快照 | 游戏存档点 |
| **branch** | 独立的开发线 | 平行宇宙，互不干扰 |
| **merge** | 合并两条分支 | 把平行宇宙合二为一 |
| **stash** | 临时藏起未完成的修改 | "先存起来，切个分支马上回来" |

---

## 2️⃣ 必会命令速查

### 📌 日常高频 10 连

```bash
git status              # 📋 看看改了啥
git diff                # 🔍 具体改了什么内容
git add <file>          # ➕ 加入暂存区
git commit -m "feat: xxx"  # 💾 保存快照
git log --oneline -10   # 📜 最近 10 条提交记录
git branch              # 🌿 查看所有分支
git checkout -b feat/xxx  # 🌱 新建并切换分支
git merge main          # 🔀 把 main 合进来
git push origin main    # 🚀 推送到 GitHub
git pull                # ⬇️ 拉取最新代码
```

### 📌 后悔药系列 🆘

```bash
# 改错了，回到上一个 commit
git checkout -- <file>          # 丢弃单个文件修改
git reset HEAD~1 --soft         # 撤销 commit，保留修改（推荐）
git reset HEAD~1 --hard         # 彻底回退，修改也丢（危险⚠️）

# commit 信息写错了
git commit --amend -m "新的提交信息"  # 修改最后一次 commit 信息

# 忘了加某个文件到上次 commit
git add forgotten_file.py
git commit --amend --no-edit    # 追加到上一次 commit
```

---

## 3️⃣ Conventional Commits（规范提交信息）

```bash
# ❌ 不规范
git commit -m "改了一下"
git commit -m "fix"
git commit -m "更新"

# ✅ 规范格式：<type>: <简短描述>
git commit -m "feat: 添加 LLM 统一客户端"        # 新功能
git commit -m "fix: 修复 SSE 流式断线重连问题"    # Bug 修复
git commit -m "docs: 补充 RAG 评估文档"          # 文档
git commit -m "refactor: 提取限流中间件为独立模块"  # 重构
git commit -m "test: 添加 Gateway 端到端测试"     # 测试
git commit -m "chore: 更新依赖版本"              # 杂务
```

| type | 含义 | 示例 |
|------|------|------|
| `feat` | 新功能 | `feat: 添加模型路由模块` |
| `fix` | Bug 修复 | `fix: 修复 token 计数溢出` |
| `docs` | 文档 | `docs: 补充 API 文档` |
| `refactor` | 重构（不改变功能） | `refactor: 提取公共验证逻辑` |
| `test` | 测试 | `test: 添加限流器单元测试` |
| `chore` | 杂务 | `chore: 升级 httpx 到 0.28` |

---

## 4️⃣ GitHub 工作流

```
           Fork (复制到自己名下)
              ↓
    git clone git@github.com:你的用户名/仓库名.git
              ↓
    git checkout -b feat/my-feature  (开新分支)
              ↓
    写代码 → git add → git commit
              ↓
    git push origin feat/my-feature
              ↓
    在 GitHub 上创建 Pull Request (PR)
              ↓
    Review → 修改 → 合并到 main 🌟
```

### 📌 .gitignore 必备模板

```gitignore
# Python
__pycache__/
*.py[cod]
.venv/
*.egg-info/

# Jupyter
.ipynb_checkpoints/

# macOS
.DS_Store

# 模型文件（太大，不进 Git！）
*.gguf
*.bin
*.pt
*.safetensors

# 敏感信息
.env
*.key
secret*
```

---

## 5️⃣ SSH 配置（免密推送）

### 📌 为什么要配 SSH？

用 HTTPS 地址每次 push 都要输用户名密码。配好 SSH 后**一次配置，永久免密**。

```bash
# 1. 生成 SSH 密钥（如果已有可跳过）
ssh-keygen -t ed25519 -C "你的邮箱@example.com"
# 一路回车即可

# 2. 复制公钥
cat ~/.ssh/id_ed25519.pub
# 复制输出的整段内容

# 3. 粘贴到 GitHub
# GitHub → Settings → SSH and GPG keys → New SSH key
# Title: 随便填（如 "我的 MacBook"）
# Key: 粘贴刚才复制的内容

# 4. 测试
ssh -T git@github.com
# 看到 "Hi 你的用户名!" 就成功了 🎉
```

### 📌 SSH Config 管理多台机器

```bash
# ~/.ssh/config
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519

Host my-server
    HostName 123.45.67.89
    User ubuntu
    IdentityFile ~/.ssh/cloud_server_key
    Port 22

# 然后直接 ssh my-server 即可，不用记 IP
```

---

## 6️⃣ 常见翻车现场 🚨

| 现象 | 原因 | 解决 |
|------|------|------|
| `git push` 报 403 | 用的 HTTPS 地址，没权限 | 改用 SSH：`git remote set-url origin git@github.com:用户名/仓库.git` |
| `git push` 报冲突 | 别人先 push 了 | `git pull --rebase` → 解决冲突 → `git push` |
| `merge conflict` | 两个人改了同一行 | 手动编辑冲突文件 → `git add` → `git commit` |
| commit 里带了 `.env` | 忘了加 .gitignore | **立即改密码** + `git rm --cached .env` + 重新 .gitignore |
| 误 commit 到 main | 应该在分支上开发 | `git checkout -b feat/xxx` → `git checkout main` → `git reset HEAD~1` |

> ⚠️ **铁律**：敏感信息（API Key、密码）一旦提交到 GitHub 就视为泄露，即使删除 commit 也可能被别人看到过。

---

## 7️⃣ AI 编程工具流（Claude Code / Cursor）

```text
# 🔥 工程级 Prompt 写法（不是"帮我写个函数"）

✅ 好的：
"在 phase0_foundation/01_python_review.md 文件中，
在'生成器'章节后面，添加一个 @retry 装饰器的完整示例，
包含异常处理和日志输出，不超过 30 行代码"

❌ 差的：
"帮我写个重试的代码"
```

| 工具 | 擅长 | 使用场景 |
|------|------|----------|
| **Claude Code** | 读项目、修 Bug、写测试、写文档 | 工程级任务 |
| **Cursor** | Tab 补全、Cmd+K 编辑、多文件 | 日常编码 |
| **GitHub Copilot** | 行级补全 | 快速写样板代码 |

---

## ✅ 产出物 Checklist

- [ ] 创建 GitHub 仓库 `llm-fullstack-roadmap`
- [ ] 配置 SSH 免密推送
- [ ] 完成第一次 commit + push（使用 Conventional Commits 格式）
- [ ] 用 `.gitignore` 排除 `__pycache__`、`.env`、`.ipynb_checkpoints`
- [ ] 在 GitHub 上看到自己的绿点 ✅
