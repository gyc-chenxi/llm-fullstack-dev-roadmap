"""
Gateway 侧指标端点
-----------------
提供网关自身的运营指标（请求数、错误率、延迟等），与 llama-server 的 /metrics
（模型性能指标：prompt tokens、predicted tokens、slot 利用率）互补。

指标来源说明：
  - llama-server 暴露模型级别的指标（prompt tokens/s, slot utilization 等）
  - Gateway 暴露代理级别的指标（请求总数、错误率、上游延迟分布）
  - 生产环境应使用 prometheus_client 库的 Counter/Histogram，
    这里做轻量级进程内快照，供 Prometheus textfile collector 或简单 curl 采集。

数据流：
  curl GET /gateway/metrics
    → gateway_metrics() 读取进程内计数器
    → 返回 JSON: {
        "uptime_seconds": float,       ← Gateway 进程已运行时长
        "requests_total": int,         ← 累计处理请求数（进程重启后重置）
        "errors_total": int,           ← 累计错误数
        "error_rate": float,           ← 错误率 = errors_total / requests_total
        "last_latency_ms": float,      ← 最近一次上游请求的延迟（毫秒）
        "rate_limit_enabled": bool      ← 速率限制是否启用
      }

指标矩阵（与上游互补）：
                     | Gateway 侧             | llama-server 侧
                     | (gateway/metrics)     | (/metrics)
  ───────────────────┼───────────────────────┼──────────────────────
  请求总数           | ✓ requests_total       | ✓ prompt_tokens_total
  错误率            | ✓ error_rate           | ✗
  首 token 延迟      | 需通过 bench 脚本获取  | ✓ predicted_tokens_seconds
  KV cache 利用率    | ✗                     | ✓ kv_cache_usage_ratio
  slot 利用率        | ✗                     | ✓ slot_used / slot_total
"""

import time

from fastapi import APIRouter

router = APIRouter(tags=["observability"])

# 进程内计数器（进程重启后重置 — 本地开发可接受）
_started_at = time.time()
_request_count = 0
_error_count = 0
_last_latency_ms: float = 0.0


def record_request(latency_ms: float, is_error: bool = False) -> None:
    """
    记录一次上游请求的指标。
    由路由处理函数在每次上游调用完成后调用。

    参数：
      latency_ms: 上游请求的端到端延迟（毫秒）
      is_error:   本次请求是否出错
    """
    global _request_count, _error_count, _last_latency_ms
    _request_count += 1
    if is_error:
        _error_count += 1
    _last_latency_ms = latency_ms


@router.get("/gateway/metrics")
async def gateway_metrics():
    """返回 Gateway 运营指标的 JSON 快照。"""
    uptime = time.time() - _started_at
    return {
        "uptime_seconds": round(uptime, 1),
        "requests_total": _request_count,
        "errors_total": _error_count,
        "error_rate": round(_error_count / max(_request_count, 1), 4),
        "last_latency_ms": _last_latency_ms,
        "rate_limit_enabled": False,
    }
