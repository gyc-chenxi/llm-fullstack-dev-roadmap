"""
Checkpoint 恢复演示
=====================

演示 LangGraph Checkpoint 的核心特性：断点恢复。

数据流：
  1. 从 SQLite 读取指定 thread_id 的 checkpoint state
  2. 打印完整状态 JSON（含所有中间节点的输出）
  3. 确认 graph 可以从该 checkpoint 继续执行

用法：
  python scripts/05_checkpoint_resume_demo.py --thread-id <thread_id>
"""

from __future__ import annotations

import argparse
import json

from langgraph_enterprise_rag.graph.builder import build_graph
from langgraph_enterprise_rag.graph.checkpoints import build_sqlite_checkpointer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LangGraph checkpoint resume demo.")
    parser.add_argument("--thread-id", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    checkpointer = build_sqlite_checkpointer()
    graph = build_graph(checkpointer=checkpointer)

    config = {"configurable": {"thread_id": args.thread_id}}
    state = graph.get_state(config)

    if state is None or not state.values:
        print(f"[checkpoint] not found thread_id={args.thread_id}")
        print("[hint] call /v1/rag/invoke or /v1/rag/stream first.")
        return

    print(f"[checkpoint] found thread_id={args.thread_id}")
    print("[checkpoint] latest state loaded")
    print(json.dumps(state.values, ensure_ascii=False, indent=2, default=str))
    print("[resume] graph can continue from checkpoint")


if __name__ == "__main__":
    main()
