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

    now = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"metrics_{now}.txt"

    r = httpx.get(args.url, timeout=10)
    r.raise_for_status()

    out_path.write_text(r.text, encoding="utf-8")
    print(f"saved: {out_path}")


if __name__ == "__main__":
    main()