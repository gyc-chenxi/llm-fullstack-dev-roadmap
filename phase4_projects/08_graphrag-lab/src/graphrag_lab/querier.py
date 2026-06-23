#!/usr/bin/env python3
"""GraphRAG query wrapper with error handling and result formatting.

Encapsulates the `graphrag query` CLI behind a clean Python API,
with automatic method selection (global vs local) based on query type.

Usage:
    from graphrag_lab.querier import GraphRAGQuerier
    q = GraphRAGQuerier(root=".")
    answer = q.query("What is a Transformer?", method="local")
    print(answer)
"""

import subprocess
import sys
import time
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class GraphRAGQuerier:
    """Thin wrapper around the `graphrag query` CLI."""

    def __init__(self, root: str = "."):
        self.root = str(Path(root).resolve())
        self._verify_index()

    def _verify_index(self):
        """Check that index artifacts exist."""
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
        """Execute a GraphRAG query.

        Args:
            query: Natural language query string.
            method: 'global' (community-level) or 'local' (entity-centric).

        Returns:
            (answer_text, elapsed_seconds)
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
        """Community-level summary search."""
        return self.query(query, method="global")

    def local_search(self, query: str) -> tuple[str, float]:
        """Entity-centric traversal search."""
        return self.query(query, method="local")

    def auto_query(self, query: str, query_type: str = "factual") -> tuple[str, float]:
        """Auto-select method based on query type.

        factual/multi_hop → local search
        global/summary → global search
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
