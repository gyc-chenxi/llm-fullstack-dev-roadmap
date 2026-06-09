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
    idx: int
    ok: bool
    status_code: int | None
    ttft_ms: float | None
    total_ms: float
    output_chars: int
    approx_tokens_per_s: float | None
    error: str | None


def percentile(values: list[float], p: float) -> float | None:
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
    通过 SSE 流式响应测 TTFT。
    TTFT = request 发出后，到收到第一个有效 data chunk 的时间。
    tokens/s 这里用字符粗估，不替代真实 tokenizer 统计；
    企业报告中应优先使用 llama-server /metrics 的 predicted_tokens_seconds。
    """
    payload: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": "你是严谨的 AI Infra 工程师，回答要结构化。"},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True,
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
                    # 上游偶发非 JSON 行不要让整个压测崩掉，记录即可。
                    pass

        total = time.perf_counter() - start
        output = "".join(output_parts)
        approx_tokens = max(len(output) / 2.0, 1.0)  # 中文粗略估算
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000/v1/chat/completions")
    parser.add_argument("--model", default="local-qwen2.5-7b-q4")
    parser.add_argument("--concurrency", type=int, default=2)
    parser.add_argument("--requests", type=int, default=10)
    parser.add_argument("--max-tokens", type=int, default=256)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--prompt", default="用五点解释 GGUF、KV Cache、Prompt Cache、Metal 后端和 continuous batching 的关系。")
    parser.add_argument("--out", default="reports/bench_results.jsonl")
    args = parser.parse_args()

    limits = httpx.Limits(
        max_connections=args.concurrency + 2,
        max_keepalive_connections=args.concurrency + 2,
    )

    timeout = httpx.Timeout(connect=5.0, read=600.0, write=30.0, pool=30.0)

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

    with open(args.out, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(asdict(r), ensure_ascii=False) + "\n")
        f.write(json.dumps({"summary": summary}, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    asyncio.run(main())