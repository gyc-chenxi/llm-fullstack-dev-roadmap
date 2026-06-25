"""
并发压测脚本：测量 AI Gateway 的 TTFT、吞吐量和错误率
=====================================================

用途：
  在生产上线前评估 Gateway + llama-server 链路的负载能力，
  特别关注首 token 延迟（TTFT）——用户体验的关键指标。

数据流向：
  脚本 → N 个并发 httpx 请求 → Gateway (http://127.0.0.1:8000)
    → llama-server (upstream) → SSE 流式响应
  ← 解析每个响应的 TTFT、总耗时、输出字符数
  ← 汇总统计：P50/P95 TTFT、平均 tokens/s、错误率
  ← 结果写入 reports/bench_results.jsonl

指标定义：
  - TTFT (Time To First Token)：从请求发出到收到第一个有效 data chunk 的时间
  - approx_tokens_per_s：通过字符数/2（中文）粗估，不替代真实 tokenizer
  - 企业级报告中应优先使用 llama-server /metrics 的 predicted_tokens_seconds

运行：
  # 先启动 Gateway + llama-server
  # 终端1：llama-server ...  # 启动上游
  # 终端2：cd gateway && python app.py
  # 终端3：
  python scripts/bench_concurrency.py \
    --concurrency 2 --requests 10 --max-tokens 256
"""

import argparse
import asyncio
import json
import statistics
import time
from dataclasses import dataclass, asdict
from typing import Any

import httpx


@dataclass
class BenchResult:
    """单次请求的压测记录。"""
    idx: int                    # 请求编号，用于追踪日志
    ok: bool                    # 是否成功（无异常）
    status_code: int | None     # HTTP 状态码，失败时为 None
    ttft_ms: float | None       # 首 token 延迟（毫秒），失败时为 None
    total_ms: float             # 请求总耗时（毫秒）
    output_chars: int           # 输出字符总数
    approx_tokens_per_s: float | None  # 估算的每秒 token 生成数
    error: str | None           # 异常信息（成功时为 None）


def percentile(values: list[float], p: float) -> float | None:
    """计算百分位值（如 P95 = percentile(data, 0.95)）。"""
    if not values:
        return None
    values = sorted(values)
    k = int((len(values) - 1) * p)
    return values[k]


async def run_one(
    client: httpx.AsyncClient,
    idx: int,
    url: str,
    model: str,
    prompt: str,
    max_tokens: int,
    temperature: float,
) -> BenchResult:
    """
    单次并发请求的执行逻辑。

    通过 SSE 流式响应测量 TTFT：
    1. 记录请求发起时间戳 start
    2. 逐行读取 SSE 事件流，识别 data: 前缀的行
    3. 解析 delta.content 累积输出文本
    4. 读取到第一个有效 content 时记录 first_token_at
    5. TTFT = first_token_at - start
    6. decode_s = total - TTFT（生成阶段的耗时，用于估算 tokens/s）

    异常处理：任何 httpx/JSON 异常均被捕获记录，不会导致整个压测中断。
    """
    payload: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": "你是严谨的 AI Infra 工程师，回答要结构化。"},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True,  # 强制流式以测量 TTFT
    }

    start = time.perf_counter()
    first_token_at: float | None = None
    output_parts: list[str] = []

    try:
        async with client.stream("POST", url, json=payload) as resp:
            status_code = resp.status_code
            resp.raise_for_status()

            async for line in resp.aiter_lines():
                if not line:
                    continue
                if not line.startswith("data: "):
                    continue

                data = line.removeprefix("data: ").strip()
                if data == "[DONE]":
                    break

                if first_token_at is None:
                    first_token_at = time.perf_counter()

                try:
                    obj = json.loads(data)
                    delta = obj.get("choices", [{}])[0].get("delta", {})
                    content = delta.get("content")
                    if content:
                        output_parts.append(content)
                except json.JSONDecodeError:
                    # 上游偶发的非 JSON 行不应使整个压测崩溃，记录并跳过
                    pass

        total = time.perf_counter() - start
        output = "".join(output_parts)
        # 中文 token 数粗略估算：字符数 ÷ 2
        approx_tokens = max(len(output) / 2.0, 1.0)
        decode_s = max(total - ((first_token_at or start) - start), 1e-6)

        return BenchResult(
            idx=idx,
            ok=True,
            status_code=status_code,
            ttft_ms=round(((first_token_at or start) - start) * 1000, 2),
            total_ms=round(total * 1000, 2),
            output_chars=len(output),
            approx_tokens_per_s=round(approx_tokens / decode_s, 2),
            error=None,
        )

    except Exception as e:
        total = time.perf_counter() - start
        return BenchResult(
            idx=idx,
            ok=False,
            status_code=None,
            ttft_ms=None,
            total_ms=round(total * 1000, 2),
            output_chars=0,
            approx_tokens_per_s=None,
            error=repr(e),
        )


async def main():
    """
    主入口：参数解析 → 创建 httpx 连接池 → 信号量控制并发 →
    as_completed 收集结果 → 统计汇总 → 输出到终端和 JSONL 文件。
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000/v1/chat/completions")
    parser.add_argument("--model", default="local-qwen2.5-7b-q4")
    parser.add_argument("--concurrency", type=int, default=2, help="并发请求数")
    parser.add_argument("--requests", type=int, default=10, help="总请求数")
    parser.add_argument("--max-tokens", type=int, default=256)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--prompt", default="用五点解释 GGUF、KV Cache、Prompt Cache、Metal 后端和 continuous batching 的关系。")
    parser.add_argument("--out", default="reports/bench_results.jsonl")
    args = parser.parse_args()

    # httpx 连接池限制：允许多个并发连接 + keepalive 复用
    limits = httpx.Limits(
        max_connections=args.concurrency + 2,
        max_keepalive_connections=args.concurrency + 2,
    )

    # 流式响应可能持续较长时间，read_timeout 设为 600s
    timeout = httpx.Timeout(connect=5.0, read=600.0, write=30.0, pool=30.0)

    # 信号量控制实际发起的并发请求数
    sem = asyncio.Semaphore(args.concurrency)
    results: list[BenchResult] = []

    async with httpx.AsyncClient(timeout=timeout, limits=limits) as client:
        async def guarded(i: int):
            async with sem:
                return await run_one(
                    client=client,
                    idx=i,
                    url=args.url,
                    model=args.model,
                    prompt=f"{args.prompt}\n请求编号：{i}",
                    max_tokens=args.max_tokens,
                    temperature=args.temperature,
                )

        tasks = [guarded(i) for i in range(args.requests)]
        for coro in asyncio.as_completed(tasks):
            r = await coro
            results.append(r)
            print(asdict(r), flush=True)

    # ── 统计汇总 ──
    ok = [r for r in results if r.ok]
    ttft = [r.ttft_ms for r in ok if r.ttft_ms is not None]
    total = [r.total_ms for r in ok]
    tps = [r.approx_tokens_per_s for r in ok if r.approx_tokens_per_s is not None]

    summary = {
        "requests": args.requests,
        "concurrency": args.concurrency,
        "success": len(ok),
        "error": args.requests - len(ok),
        "ttft_ms_p50": statistics.median(ttft) if ttft else None,
        "ttft_ms_p95": percentile(ttft, 0.95),
        "total_ms_p50": statistics.median(total) if total else None,
        "total_ms_p95": percentile(total, 0.95),
        "approx_tps_avg": round(statistics.mean(tps), 2) if tps else None,
    }

    print("\nSUMMARY")
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    # 写出 JSONL 格式的完整结果（便于后续可视化或对比分析）
    with open(args.out, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(asdict(r), ensure_ascii=False) + "\n")
        f.write(json.dumps({"summary": summary}, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    asyncio.run(main())