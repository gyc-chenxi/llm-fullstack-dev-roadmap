"""
SQLite Checkpoint 持久化
==========================

LangGraph 的 checkpoint 机制允许将每次节点执行后的状态保存到 SQLite，
支持：
  1. 对话状态持久化：服务重启后可以通过 thread_id 恢复状态
  2. 断点重放：查看历史状态快照，诊断 graph 执行路径
  3. 分叉恢复：从任意 checkpoint 继续执行

为什么用 SQLite 而非内存：
  - 服务重启后内存状态丢失
  - 多轮对话需要跨请求保持上下文
  - 调试和审计需要可追溯的执行历史

LANGGRAPH_STRICT_MSGPACK=true：
  启用更严格的 msgpack 反序列化策略，避免恶意 payload 导致反序列化漏洞。
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver


_CONN: sqlite3.Connection | None = None


def build_sqlite_checkpointer() -> SqliteSaver:
    """构建 SQLite 持久化 checkpointer。

    使用 check_same_thread=False 允许多线程访问（FastAPI 异步场景需要）。
    首次调用 setup() 初始化数据库表结构（部分版本会在首次 put 时自动初始化）。
    """
    global _CONN

    os.environ.setdefault("LANGGRAPH_STRICT_MSGPACK", "true")

    db_path = Path(os.getenv("CHECKPOINT_DB", "data/checkpoints/langgraph.sqlite"))
    db_path.parent.mkdir(parents=True, exist_ok=True)

    _CONN = sqlite3.connect(
        str(db_path),
        check_same_thread=False,
    )

    saver = SqliteSaver(_CONN)

    try:
        saver.setup()
    except Exception:
        pass

    return saver