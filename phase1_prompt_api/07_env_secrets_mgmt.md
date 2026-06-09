# 🔐 07 — API Key 管理与安全

> 🎯 **目标**：学会安全地管理 API Key，避免泄露到 GitHub。
> ⏱️ 预计时间：0.5 天

---

## 📋 为什么 API Key 管理是大模型开发的必修课？

| 事故 | 后果 | 真实案例 |
|------|------|----------|
| Key 推到 GitHub | 被爬虫扫到，盗刷费用 | 每天都有 AWS/OpenAI Key 泄露事件 |
| Key 硬编码在代码里 | 换环境/换电脑就失效 | 常见新手错误 |
| Key 在截图中泄露 | 从截图 OCR 提取 Key | 多人发推特时露出 API Key |
| Key 和同事共享 | 不知道谁花了多少钱 | 账单纠纷 |

---

## 1️⃣ 各平台 API Key 申请流程

### OpenAI

```
1. 打开 https://platform.openai.com/api-keys
2. 注册/登录 → 邮箱验证
3. 左侧「API keys」→「Create new secret key」
4. 复制 Key（以 sk- 开头，只显示一次！）
5. ⚠️ 新号有免费额度（$5），用完后需绑卡充值
6. 设置 Usage Limits：https://platform.openai.com/usage → 月预算上限
```

### DeepSeek

```
1. 打开 https://platform.deepseek.com/api_keys
2. 手机号注册/登录
3. 创建 API Key → 复制 sk-xxx
4. 充值（最低 ¥10）
5. 价格极低：DeepSeek-V3 约 ¥1/1M input tokens
```

### Qwen / 阿里云 DashScope

```
1. 打开 https://dashscope.console.aliyun.com/
2. 支付宝/淘宝扫码登录阿里云
3. 左侧「API-KEY 管理」→ 创建
4. ⚠️ DashScope 的 Key 不是 RAM 的 AccessKey！是独立的 API Key
5. 新用户有免费额度（100 万 tokens/月）
```

### Claude / Anthropic

```
1. 打开 https://console.anthropic.com/
2. 邮箱注册 → 验证
3. 「API Keys」→「Create Key」
4. Key 以 sk-ant- 开头
5. 需绑卡充值（有 $5 免费额度）
```

---

## 2️⃣ .env 文件使用规范

### 📌 黄金规则

```
.env           ← ⛔ 绝对不能进 Git！（包含真实 Key）
.env.example   ← ✅ 可以进 Git（Key 用占位符）
```

```bash
# .env.example（给队友看的模板）
OPENAI_API_KEY=sk-your-key-here
DEEPSEEK_API_KEY=sk-your-key-here
GATEWAY_API_KEY=change-me

# .env（你的本地文件，只在 .gitignore 里）
OPENAI_API_KEY=sk-proj-AbCdEf1234567890
DEEPSEEK_API_KEY=sk-XyZ0987654321
GATEWAY_API_KEY=my-real-secret-key
```

### 📌 .gitignore 配置

```gitignore
# 环境变量
.env
.env.local
.env.production

# 但保留模板文件
!.env.example
```

### 📌 验证 .env 不会被提交

```bash
# 提交前检查
git status | grep .env
# 应该只看到 .env.example，不应该看到 .env

# 如果 .env 已经被 commit 了
git rm --cached .env
git commit -m "chore: remove .env from git tracking"
# ⚠️ 然后立即去各平台 revoke 泄露的 Key！
```

---

## 3️⃣ python-dotenv 使用

```python
# 安装
# pip install python-dotenv

import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 读取（带默认值）
openai_key = os.getenv("OPENAI_API_KEY")
if not openai_key:
    raise ValueError("请在 .env 中设置 OPENAI_API_KEY")

# 🔥 更推荐：pydantic-settings 自动加载
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    deepseek_api_key: str = ""       # 可选 Key

    model_config = {"env_file": ".env"}

settings = Settings()
print(f"Provider: OpenAI, Key loaded: {bool(settings.openai_api_key)}")
```

---

## 4️⃣ 临时 Key 安全实践

### 📌 分享代码前自动清除 Key

```bash
#!/bin/bash
# clean_for_share.sh — 分享代码前执行

# 1. 检查是否有硬编码 Key
grep -r "sk-" . --exclude-dir=.venv --exclude-dir=.git --exclude="*.md" && echo "⚠️ 发现疑似 API Key！" || echo "✅ 未发现硬编码 Key"

# 2. 确认 .gitignore 包含 .env
grep -q "^\.env$" .gitignore || echo ".env" >> .gitignore

# 3. 检查 git 暂存区是否有 .env
git ls-files --cached | grep \.env$ && echo "⚠️ .env 被 git 追踪中！执行 git rm --cached .env" || echo "✅ .env 未被追踪"
```

### 📌 macOS 钥匙串集成（高级）

```bash
# 将 Key 存到钥匙串而非 .env 文件
security add-generic-password -a "openai" -s "llm-api-keys" -w "sk-xxx"

# Python 读取钥匙串
import subprocess

def get_key_from_keychain(service: str, account: str) -> str:
    result = subprocess.run(
        ["security", "find-generic-password", "-a", account, "-s", service, "-w"],
        capture_output=True, text=True,
    )
    return result.stdout.strip()

api_key = get_key_from_keychain("llm-api-keys", "openai")
```

---

## 5️⃣ API Key 轮换策略

```python
import os, random

class APIKeyPool:
    """Key 池：多 Key 轮询，避免单个 Key 超限额"""

    def __init__(self, env_prefix: str = "OPENAI_API_KEY"):
        self.keys = []
        for key, value in os.environ.items():
            if key.startswith(env_prefix) and value:
                self.keys.append(value)

    def get_key(self) -> str:
        if not self.keys:
            raise RuntimeError("没有可用的 API Key")
        return random.choice(self.keys)  # 可改为 Round-Robin

# .env 中：
# OPENAI_API_KEY_1=sk-xxx
# OPENAI_API_KEY_2=sk-yyy
# OPENAI_API_KEY_3=sk-zzz

pool = APIKeyPool()
key = pool.get_key()  # 随机取一个
```

---

## 6️⃣ 各平台费用控制

| 平台 | 限费设置位置 | 建议 |
|------|------------|------|
| OpenAI | Usage Limits → Monthly Budget | 学习阶段设 $10/月 |
| DeepSeek | 余额用完自动停 | 充值 ¥20，用完再说 |
| Qwen | DashScope 控制台 | 免费额度够学习用 |
| Claude | Usage Limits | 设 $5/月 |

---

## 🚨 翻车现场

| 现象 | 原因 | 解决 |
|------|------|------|
| Key 推到 GitHub → 收到扣费告警 | .env 没在 .gitignore | 立即 revoke Key → git rm --cached .env → 重新 commit |
| CI/CD 里 Key 不生效 | GitHub Secrets 没配 | Settings → Secrets → Actions → 添加 |
| Key 在截图里泄露 | 发社交媒体时没注意 | 🔴 裁剪截图前检查，或模糊处理 |
| `load_dotenv()` 不生效 | 路径不对或 .env 编码问题 | `load_dotenv(verbose=True)` 看加载日志 |
| 多人共用一个 Key | 不知道谁花了多少钱 | 每人独立 Key，或 Key Pool + 日志追踪 |

---

## ✅ 产出物 Checklist

- [ ] 创建 `.env.example` 和 `.env`（.env 在 .gitignore 中）
- [ ] 在 OpenAI/DeepSeek 平台注册并创建 API Key
- [ ] 用 `python-dotenv` 或 `pydantic-settings` 加载 Key
- [ ] 运行 `clean_for_share.sh` 确保没有硬编码 Key
- [ ] 验证 `git status` 不显示 `.env`
