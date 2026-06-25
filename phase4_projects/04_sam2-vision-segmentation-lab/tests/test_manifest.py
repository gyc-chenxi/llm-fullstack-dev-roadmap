"""
单元测试：Manifest 记录器
=========================

测试范围：
  - append_manifest() 能正确追加写入 JSONL
  - 自动注入 created_at 时间戳

测试策略：
  使用 tempfile 避免污染真实工程数据。
"""

import json
import tempfile
from pathlib import Path

from sam2_lab.utils.manifest import append_manifest


def test_append_manifest():
    """使用临时文件测试 JSONL 追加写入和时间戳注入。"""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = tmp.name

    record = {"image": "test.jpg", "score": 0.99}

    append_manifest(tmp_path, record)

    with open(tmp_path, encoding="utf-8") as f:
        lines = f.readlines()
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["image"] == "test.jpg"
        assert "created_at" in data  # 验证自动注入时间戳

    Path(tmp_path).unlink()