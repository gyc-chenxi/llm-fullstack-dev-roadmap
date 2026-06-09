# 🐳 07 — Docker 与中间件入门

> 🎯 **目标**：学会用 Docker 启动开发环境，理解 Redis/PostgreSQL 在大模型系统中的角色。
> ⏱️ 预计时间：1 天

---

## 📋 为什么大模型开发要学 Docker？

| 痛点 | 没有 Docker | 有了 Docker |
|------|-----------|------------|
| 环境不一致 | "我电脑上能跑啊" | 镜像锁定环境，去哪都一样 |
| 中间件安装 | Redis、PG、Chroma 一个个装 | `docker compose up` 一键启动全部 |
| 模型部署 | 手动配置 CUDA、依赖、端口 | Dockerfile 写好，一键部署 |
| 团队协作 | 发环境配置文档（没人看） | `docker compose up` 就完了 |

> 🍎 **Mac 用户注意**：Docker Desktop for Mac 无法直通 GPU。本地推理仍在宿主机跑，Docker 只用来跑 API 服务 + 中间件（Redis/PG）。

---

## 1️⃣ Docker 核心概念速查

| 概念 | 一句话 | 类比 |
|------|--------|------|
| **镜像 (Image)** | 应用 + 所有依赖的快照 | 安装包 `.dmg` |
| **容器 (Container)** | 镜像的运行实例 | 打开后的 App |
| **Dockerfile** | 镜像的构建蓝图 | Makefile / 配方 |
| **Volume** | 数据持久化（容器删了数据还在） | 外接硬盘 |
| **Network** | 容器间通信 | 局域网 |
| **Docker Compose** | 一键编排多个容器 | 全家桶套餐 |

---

## 2️⃣ Dockerfile 编写

```dockerfile
# 📌 基础 FastAPI 镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 先复制依赖文件（利用 Docker 缓存层 🔑）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 再复制代码（经常变，放后面避免破坏缓存）
COPY . .

# 声明端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 📌 多阶段构建（减体积）

```dockerfile
# 阶段 1：编译（体积大，用完就扔）
FROM python:3.11 AS builder
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# 阶段 2：运行（只保留运行时需要的东西）
FROM python:3.11-slim
COPY --from=builder /root/.local /root/.local
COPY . /app
WORKDIR /app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
# 最终镜像体积可能从 1GB 降到 300MB 📉
```

---

## 3️⃣ 必会命令

```bash
# 🔨 构建镜像
docker build -t my-api:v1 .

# 🏃 运行容器
docker run -d -p 8000:8000 --name my-api my-api:v1

# 👀 查看状态
docker ps                  # 运行中的容器
docker ps -a               # 全部容器（含已停止）
docker logs -f my-api      # 实时看日志

# 🛑 停止与清理
docker stop my-api
docker rm my-api           # 删除容器（镜像还在）
docker rmi my-api:v1       # 删除镜像

# 🔍 进入容器调试
docker exec -it my-api bash
```

---

## 4️⃣ Docker Compose：全家桶一键启动

### 📌 大模型开发标准 docker-compose.yml

```yaml
version: "3.9"

services:
  # 🧠 API 网关
  api:
    build: ./final_ai_gateway
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      redis:
        condition: service_healthy
      db:
        condition: service_healthy
    restart: unless-stopped

  # ⚡ Redis：限流 / 缓存 / 会话
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 3

  # 🗄️ PostgreSQL：用户 / 日志 / 用量
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: llm
      POSTGRES_PASSWORD: secret_change_me
      POSTGRES_DB: gateway
    ports:
      - "5432:5432"
    volumes:
      - pg_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql  # 初始化脚本
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U llm"]
      interval: 5s
      timeout: 3s
      retries: 3

volumes:
  redis_data:
  pg_data:
```

### 📌 关键参数解释

| 配置项 | 含义 | 为什么重要 |
|--------|------|-----------|
| `depends_on` + `condition: service_healthy` | 等 Redis/PG 就绪后才启动 API | 否则 API 连不上数据库 |
| `restart: unless-stopped` | 容器挂了自动重启 | 生产必备 |
| `volumes` | 数据存在宿主机，删容器不丢数据 | 数据库持久化 |
| `healthcheck` | Docker 知道容器是否真正可用 | 配合 `depends_on` |

---

## 5️⃣ 在大模型系统中各中间件的角色

| 中间件 | 在大模型系统中做什么 | 代码示例 |
|--------|---------------------|----------|
| **Redis** | 🔢 限流计数器<br>💬 对话缓存<br>📡 Pub/Sub 消息推送<br>🔑 Session 存储 | `INCR user:123:count`<br>`EXPIRE user:123:count 60` |
| **PostgreSQL** | 👤 用户表<br>🔑 API Key 表<br>📊 Token 用量记录<br>📝 日志持久化 | `SELECT SUM(tokens) FROM usage WHERE user_id=123` |
| **向量数据库<br>(Chroma/FAISS)** | 🔍 相似度检索<br>📚 知识库存储 | `collection.query(texts=["什么是 RAG?"])` |

---

## 6️⃣ Redis 快速上手

```bash
# 启动 Redis 容器
docker run -d --name redis -p 6379:6379 redis:7-alpine

# 进入 Redis CLI
docker exec -it redis redis-cli
```

```redis
# 📌 基础命令
SET key "hello"         # 设值
GET key                 # 取值 → "hello"
DEL key                 # 删值
EXPIRE key 60           # 60 秒后自动过期 ⏱️
TTL key                 # 查看剩余秒数

# 🔢 计数器（限流核心）
INCR user:999:count     # +1 → 返回新值
EXPIRE user:999:count 60  # 60 秒后重置

# 📋 列表（消息队列）
LPUSH queue "task1"     # 左边插入
RPOP queue              # 右边取出 → "task1"
```

### 🔥 滑动窗口限流（Redis 版伪代码）

```python
async def check_rate_limit(user_id: str, max_req: int = 30, window: int = 60):
    """用户每分钟最多 max_req 次请求"""
    key = f"rate_limit:{user_id}"
    current = await redis.incr(key)
    if current == 1:
        await redis.expire(key, window)
    if current > max_req:
        raise HTTPException(429, "请求太频繁，请稍后再试 ⚠️")
```

---

## 7️⃣ PostgreSQL 快速上手

```bash
# 启动 PG 容器
docker run -d --name pg \
  -e POSTGRES_USER=llm \
  -e POSTGRES_PASSWORD=secret \
  -e POSTGRES_DB=gateway \
  -p 5432:5432 \
  postgres:16-alpine

# 进入 PG
docker exec -it pg psql -U llm -d gateway
```

```sql
-- 📌 基础 DDL
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    api_key VARCHAR(64) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE usage_logs (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    model VARCHAR(50),
    input_tokens INT,
    output_tokens INT,
    cost NUMERIC(10, 6),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 📊 常用查询
-- 今日各模型调用量
SELECT model, COUNT(*), SUM(input_tokens + output_tokens) AS total_tokens
FROM usage_logs
WHERE created_at >= CURRENT_DATE
GROUP BY model;

-- 某用户本月费用
SELECT SUM(cost) FROM usage_logs
WHERE user_id = 1
  AND created_at >= DATE_TRUNC('month', CURRENT_DATE);
```

---

## 8️⃣ 常见翻车现场 🚨

| 现象 | 原因 | 解决 |
|------|------|------|
| 容器启动后立刻退出 | 前台进程结束了 | `CMD` 必须是前台运行的命令（如 `uvicorn`） |
| `docker compose up` 端口冲突 | Mac 的 AirPlay 占 5000 / 其他服务占端口 | 改端口映射 `"8081:8000"` |
| 容器内无法连 `localhost` | 每个容器有独立网络 | 用服务名（如 `redis`、`db`），Docker Compose 自动 DNS |
| 改了代码但 API 没变 | 镜像构建时复制了旧代码 | 开发阶段用 `volumes: - .:/app` 挂载代码目录 |
| Volume 数据丢失 | 没挂载 volume | `docker compose down -v` 会删 volume！不加 `-v` |
| 镜像太大（2GB+） | 基础镜像 + 无用层 | 用 `python:3.11-slim` + 多阶段构建 |

---

## 9️⃣ 常用 Docker Compose 命令

```bash
docker compose up -d          # 🚀 后台启动所有服务
docker compose ps             # 📋 查看服务状态
docker compose logs -f api    # 📜 查看 API 日志
docker compose restart api    # 🔄 重启单个服务
docker compose down           # 🛑 停止并删除容器（保留 volume）
docker compose down -v        # 💀 停止+删容器+删 volume（数据清空！）
docker compose build --no-cache  # 🔨 强制重建镜像
```

---

## ✅ 产出物 Checklist

- [ ] 安装 Docker Desktop 并验证 `docker run hello-world`
- [ ] 编写 `docker-compose.yml`，启动 FastAPI + Redis + PostgreSQL
- [ ] 验证三个服务可以互相 ping 通（`docker exec api curl redis:6379`）
- [ ] 用 `docker exec -it <容器名> bash` 进入容器调试
- [ ] 给 Redis 和 PG 配置 healthcheck
- [ ] 写一个 `docker compose up -d` 就能启动的开发环境
