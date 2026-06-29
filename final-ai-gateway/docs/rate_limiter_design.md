# ⭐ Token Bucket Rate Limiter: Redis 令牌桶限流

## 核心理念

> 限流的本质是在"允许突发"和"保护后端"之间找到平衡。令牌桶算法允许短时突发（burst）但限制长期平均速率（rate），比固定窗口计数器更优雅。

## 算法对比

```
Token Bucket (本实现):         Fixed Window (简单计数器):
  时间轴:                        时间轴:
  │ ● ● ● ● ○ │                 │████████████|
  │ ● ● ○ ○ ○ │                 │██████      |
  │ ● ● ● ● ● │                 │████████████|
  │     burst=5                  │     window=60s
  │     rate=2/s                 │     max=100/60s
  
  优点: 允许突发, 平滑限流         缺点: 窗口边界有流量尖峰
  缺点: 实现略复杂                 缺点: 无法处理突发
```

## 双层层流架构

```
Layer 1: Local Token Bucket (内存级)
    ┌──────────────────────────┐
    │  每个请求先过本地桶         │
    │  rate=100/s, burst=200   │
    │  无网络开销, 纳秒级判断     │
    └──────────────────────────┘
    │ 通过?
    ├── No → 429 Too Many Requests
    │
    ▼ Yes
    │
Layer 2: Redis Token Bucket (分布式级)  
    ┌──────────────────────────┐
    │  Redis 中按 Key 维护桶    │
    │  用户级: rate=10/s        │
    │  IP级:   rate=100/s       │
    │  全局级:  rate=1000/s     │
    │  Redis EVAL 保证原子性     │
    └──────────────────────────┘
    │ 通过?
    ├── No → 429 + Retry-After header
    │
    ▼ Yes → 放行到 Admission Controller
```

## 核心代码结构 (backend/app/infrastructure/redis/redis_token_bucket.py)

```python
# Redis Token Bucket — 使用 Lua Script 保证原子性
# KEYS[1] = bucket_key, ARGV[1] = rate, ARGV[2] = burst, ARGV[3] = now, ARGV[4] = cost

LUA_SCRIPT = """
local key = KEYS[1]
local rate = tonumber(ARGV[1])
local burst = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local cost = tonumber(ARGV[4])

-- 读取当前桶状态
local data = redis.call('GET', key)
local tokens, last_refill

if data then
    local decoded = cjson.decode(data)
    tokens = decoded.tokens
    last_refill = decoded.last_refill
else
    tokens = burst
    last_refill = now
end

-- 补充令牌 (基于时间流逝)
local elapsed = now - last_refill
tokens = math.min(burst, tokens + elapsed * rate)
last_refill = now

-- 尝试消费
if tokens >= cost then
    tokens = tokens - cost
    redis.call('SET', key, cjson.encode({
        tokens = tokens,
        last_refill = last_refill
    }))
    redis.call('EXPIRE', key, 60)  -- 自动过期
    return {1, tokens}              -- {允许, 剩余令牌}
else
    redis.call('SET', key, cjson.encode({
        tokens = tokens,
        last_refill = last_refill
    }))
    return {0, tokens}              -- {拒绝, 剩余令牌}
end
"""

async def consume(self, api_key: str, cost: int = 1) -> LimiterResult:
    """两层限流: 本地桶 (快速路径) + Redis 桶 (精确控制)"""

    # Layer 1: 本地桶 (纳秒级)
    local_ok = self.local_bucket.consume(cost)
    if not local_ok:
        # 本地已限流 → 大概率 Redis 也限流, 直接返回
        return LimiterResult(allowed=False, retry_after_sec=1)

    # Layer 2: Redis 桶 (Lua 保证原子性)
    allowed, remaining = await self.redis.eval(
        LUA_SCRIPT, 1,
        f"ratelimit:{api_key}",
        self.rate, self.burst, time.time(), cost,
    )

    if not allowed:
        headers = {"Retry-After": str(int(1 / self.rate))}
        return LimiterResult(allowed=False, retry_after_sec=1/self.rate)

    return LimiterResult(allowed=True, remaining_tokens=remaining)
```

## 三层限流域名 (在 app.yaml 中配置)

```yaml
rate_limiter:
  # 第一层: 全局限流 (保护 Gateway 自身)
  global:
    rate: 500        # 每秒 500 请求
    burst: 1000      # 最多突发 1000

  # 第二层: 用户级别 (按 API Key)
  per_user:
    default:
      rate: 10       # 每秒 10 请求
      burst: 20
    premium_users:
      rate: 50
      burst: 100

  # 第三层: IP 级别 (防爬虫)
  per_ip:
    rate: 100
    burst: 200
```

## 生产级考虑

- **Redis 原子性**：使用 Lua script 保证读-计算-写的原子性，无需分布式锁
- **优雅降级**：Redis 不可用时自动退化到本地桶模式（不阻断业务）
- **热 Key 防护**：高频 Key 自动升级为本地桶缓存，减少 Redis 压力
- **Header 透传**：429 响应携带 `Retry-After`、`X-RateLimit-Remaining`、`X-RateLimit-Reset`
- **预热策略**：启动时预填充 premium 用户的桶