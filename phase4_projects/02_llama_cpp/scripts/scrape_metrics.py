"""
指标抓取脚本：定时采集 llama-server 的 Prometheus 指标快照
==========================================================

用途：
  在无法搭建完整 Prometheus + Grafana 栈的本地开发环境中，
  定期抓取 llama-server 的 /metrics 端点保存为时间戳文件，
  供后续离线分析或 Grafana 手动导入。

数据流：
  scrape_metrics.py → httpx GET → upstream llama-server:8081/metrics
    → Prometheus 文本格式的指标响应（prompt_tokens_seconds,
      predicted_tokens_seconds, slot_utilization 等）
    → 保存至 observability/metrics_snapshots/metrics_YYYYMMDD_HHMMSS.txt

与 Gateway 指标的关系：
  - scrape_metrics.py → 模型级别指标（来自 llama-server /metrics）
  - Gateway /gateway/metrics → 代理级别指标（请求数、错误率、延迟）
  两者互补，共同构成完整可观测性视图。

运行：
  python scripts/scrape_metrics.py --url http://127.0.0.1:8081/metrics
"""

import argparse
import datetime as dt
from pathlib import Path

import httpx


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8081/metrics")
    parser.add_argument("--out-dir", default="observability/metrics_snapshots")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 文件名带时间戳，确保每次抓取不覆盖历史
    now = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"metrics_{now}.txt"

    r = httpx.get(args.url, timeout=10)
    r.raise_for_status()

    out_path.write_text(r.text, encoding="utf-8")
    print(f"saved: {out_path}")


if __name__ == "__main__":
    main()