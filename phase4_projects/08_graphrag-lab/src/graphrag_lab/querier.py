"""
GraphRAG CLI Wrapper
======================

封装 `graphrag query` CLI 命令，提供干净的 Python API。

数据流：
  query(str) → graphrag CLI (subprocess)
    → local search: entity-centric traversal (多跳/事实性查询)
    → global search: community-level summary (总结/全局性查询)
    → stdout(answer) + stderr(diagnostics)

自动方法选择：
  - factual/multi_hop → local search (实体遍历检索)
  - global/summary → global search (社区级摘要)
"""

import subprocess
import sys
import time
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class GraphRAGQuerier:
    """graphrag query CLI 的轻量 Python 封装。

    通过 _verify_index() 提前检查索引状态（data/output/*.parquet）。
    """

    def __init__(self, root: str = "."):
        self.root = str(Path(root).resolve())
        self._verify_index()

    def _verify_index(self):
        """检查 data/output/ 中是否存在 parquet 索引文件。"""
        output = Path(self.root) / "data" / "output"
        if not output.exists():
            logger.warning("data/output/ not found. Index may not have been built.")
            return
        parquets = list(output.glob("*.parquet"))
        if not parquets:
            logger.warning("No parquet files in data/output/. Index may be incomplete.")
        else:
            logger.info("Index found: %d parquet files", len(parquets))

    def query(self, query: str, method: str = "local") -> tuple[str, float]:
        """执行 GraphRAG 查询。

        Args:
            query: 自然语言查询
            method: 'global' (社区级摘要) 或 'local' (实体中心遍历)

        Returns:
            (answer_text, elapsed_seconds)

        Raises:
            ValueError: method 参数不合法
            RuntimeError: graphrag CLI 返回非零退出码
        """
        if method not in ("global", "local"):
            raise ValueError(f"method must be 'global' or 'local', got '{method}'")

        cmd = [
            sys.executable, "-m", "graphrag", "query",
            "--root", self.root,
            "--method", method,
            query,
        ]

        t0 = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.root)
        elapsed = time.time() - t0

        if result.returncode != 0:
            raise RuntimeError(
                f"GraphRAG query failed (exit={result.returncode}): "
                f"{result.stderr.strip()[:300]}"
            )

        return result.stdout.strip(), elapsed

    def global_search(self, query: str) -> tuple[str, float]:
        """社区级摘要搜索（适合总结/全局性问题）。"""
        return self.query(query, method="global")

    def local_search(self, query: str) -> tuple[str, float]:
        """实体中心遍历搜索（适合多跳/事实性问题）。"""
        return self.query(query, method="local")

    def auto_query(self, query: str, query_type: str = "factual") -> tuple[str, float]:
        """根据查询类型自动选择搜索方法。

        factual/multi_hop → local search (实体级别)
        global/summary → global search (社区级别)
        """
        if query_type in ("multi_hop", "factual"):
            return self.local_search(query)
        return self.global_search(query)


# ---------------------------------------------------------------------------
# CLI for testing
# ---------------------------------------------------------------------------
def main():
    import argparse

    parser = argparse.ArgumentParser(description="GraphRAG Query CLI Wrapper")
    parser.add_argument("--root", default=".")
    parser.add_argument("--method", choices=["global", "local"], default="local")
    parser.add_argument("query", nargs="?", default=None,
                        help="Query string (interactive if omitted)")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="[querier] %(message)s")

    querier = GraphRAGQuerier(root=args.root)

    query_text = args.query
    if not query_text:
        try:
            query_text = input("Query: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return

    if not query_text:
        print("No query provided.")
        return

    answer, elapsed = querier.query(query_text, method=args.method)
    print(f"\n{'='*60}")
    print(f"Method: {args.method.upper()} | Time: {elapsed:.1f}s")
    print(f"{'='*60}")
    print(answer)
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
