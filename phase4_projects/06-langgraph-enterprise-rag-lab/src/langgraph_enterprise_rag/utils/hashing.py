"""
Stable Hash 工具
==================

SHA256 哈希取前 16 位 hex 作为文档/分块的稳定唯一标识。

为什么不用 UUID：
  - 相同内容生成相同 hash（幂等性），避免重新摄入时生成不同 ID
  - 16 字符长度在 URL / JSON 中较为紧凑
"""

from __future__ import annotations

import hashlib


def stable_hash(text: str, length: int = 16) -> str:
    """生成内容的稳定 SHA256 哈希标识。

    length=16 提供 64-bit 碰撞概率，对于万级文档场景足够安全。
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:length]
