"""API Key 鉴权 — 常量时间比较防时序攻击"""

import secrets
from fastapi import Header, HTTPException
from .config import settings


async def verify_api_key(
    x_api_key: str = Header(None, alias="X-API-Key"),
    authorization: str = Header(None),
) -> None:
    """验证 API Key — 支持 Header 和 Bearer Token 两种方式"""
    if not settings.auth_enabled or not settings.api_key:
        return

    # 支持 X-API-Key 或 Authorization: Bearer <key>
    provided_key = x_api_key
    if not provided_key and authorization and authorization.startswith("Bearer "):
        provided_key = authorization[7:]

    if not provided_key:
        raise HTTPException(
            status_code=401,
            detail={"code": "AUTH_MISSING", "message": "缺少 API Key"},
        )

    # 常量时间比较，防止时序攻击
    if not secrets.compare_digest(provided_key, settings.api_key):
        raise HTTPException(
            status_code=403,
            detail={"code": "AUTH_INVALID", "message": "API Key 无效"},
        )
