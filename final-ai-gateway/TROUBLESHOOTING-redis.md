# Troubleshooting: Redis 连接问题

## 症状

```
redis.exceptions.ConnectionError: Error connecting to Redis
```
或
```
RuntimeError: Redis pool not initialized
```

## 原因

1. Redis 服务未启动
2. Redis 端口被占用
3. Redis 密码配置错误
4. Docker Redis 容器未运行

## 解决步骤

### 1. 检查 Redis 状态

```bash
# 检查 Docker Redis 是否运行
docker ps | grep redis

# 检查本地 Redis 是否运行
redis-cli ping
# 预期输出: PONG
```

### 2. 启动 Redis

```bash
# 方式 A: Docker
make run-redis
# 或
docker-compose -f docker/docker-compose.yml up -d redis

# 方式 B: 本地安装的 Redis
redis-server --port 6379 --daemonize yes
```

### 3. 验证连接

```bash
# 测试连接
redis-cli -h localhost -p 6379 ping

# Python 测试
python -c "
import asyncio
import redis.asyncio as aioredis

async def test():
    r = aioredis.Redis.from_url('redis://localhost:6379/0')
    print(await r.ping())
    await r.aclose()

asyncio.run(test())
"
```

### 4. 检查防火墙

macOS 一般不会拦截本地回环，但确认一下：

```bash
# 检查端口是否监听
lsof -i :6379
```

### 5. 重置 Redis 数据

如果数据损坏导致问题：

```bash
redis-cli FLUSHALL
```

### 6. 检查环境变量

确保 `.env` 文件配置正确：

```bash
# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=    # 本地开发通常为空
```

## 预防措施

- 在 `docker-compose.yml` 中配置 Redis healthcheck
- 使用 `init_redis_pool()` 前先 `ping()` 验证连接
- 在 `main.py` 的 lifespan 中捕获 Redis 连接异常
