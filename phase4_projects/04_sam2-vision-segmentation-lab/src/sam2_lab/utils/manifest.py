"""
生成记录 manifest 管理
======================

将每次分割或追踪操作的元数据以 JSONL 格式追加写入文件。
每条记录自动注入 created_at 时间戳。

JSONL 格式优势：
  - 每行独立 JSON，可用 grep/jq 查询
  - 追加写入，无需加锁或维护索引
  - 易于导入 Pandas 做批量分析

数据流：
  run() → append_manifest(path, record)
    → 自动注入 created_at → 追加写入 JSONL
    → 每行: {"created_at":"2024-06-12T14:30:00","image":"test.jpg","score":0.95,...}
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def append_manifest(path: str | Path, record: dict[str, Any]) -> None:
    """
    将一条记录追加写入 JSONL manifest 文件。

    自动注入 created_at 字段（ISO 8601 格式，秒级精度），
    便于按时间进行实验比对和数据回溯。

    参数：
      path: manifest 文件路径（不存在则自动创建目录）
      record: 记录字典（如 image, score, mask_path 等字段）
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        **record,
    }

    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")