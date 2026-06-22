from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver


_CONN: sqlite3.Connection | None = None


def build_sqlite_checkpointer() -> SqliteSaver:
    global _CONN

    # 更安全的 msgpack 反序列化策略。
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
        # 部分版本会在首次 put 时自动初始化。
        pass

    return saver