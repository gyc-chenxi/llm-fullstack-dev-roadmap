"""
统一错误码与异常处理器
----------------------
设计要点：
  1. 每个错误有稳定的 code 字符串，前端/监控系统可直接 key on。
  2. HTTP 状态码存在歧义（502 可能是上游宕机或超时），code 字符串消除歧义。
  3. 全部返回 JSON，不返回 HTML — 这是 API 网关，不是 CMS。

异常处理链（按优先级）：
  RequestValidationError → validation_exception_handler    ← Pydantic 校验失败
  HTTPException          → http_exception_handler          ← 显式抛出的 HTTP 错误
  Exception              → generic_exception_handler       ← 兜底：未预料的异常

数据流向：
  上游异常 (httpx) → routes_chat 中捕获 → 以 HTTPException 重抛
    → http_exception_handler → code 映射 → JSON 响应 (ORJSONResponse)
"""

from fastapi import Request
from fastapi.responses import ORJSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

# ── 错误码注册表 ──
# 保持扁平无嵌套，方便前端/SRE 在日志/Grafana 中 grep

ERROR_CODES = {
    # 4xx — 调用方错误
    "VALIDATION_ERROR":       "Request body or query parameter failed schema validation.",
    "AUTH_MISSING":           "No API key provided in X-API-Key header.",
    "AUTH_INVALID":           "The provided API key is not valid.",
    "RATE_LIMIT_EXCEEDED":    "Too many requests.  Retry after the Retry-After seconds.",
    # 5xx — 网关或上游错误
    "UPSTREAM_TIMEOUT":       "The upstream llama-server did not respond in time.",
    "UPSTREAM_CONNECT_ERROR": "Could not connect to the upstream llama-server.",
    "UPSTREAM_HTTP_ERROR":    "The upstream returned an unexpected HTTP error.",
    "UPSTREAM_INVALID_JSON":  "The upstream returned a malformed JSON body.",
    "INTERNAL_ERROR":         "An unexpected internal error occurred.",
}

# ── 异常处理器 ──

async def validation_exception_handler(
    request: Request, exc: RequestValidationError,
) -> ORJSONResponse:
    """
    Pydantic 校验失败 → 结构化的 422 JSON 响应。
    包含详细的字段级错误信息，前端可据此高亮非法输入。
    """
    details = []
    for err in exc.errors():
        details.append({
            "loc": list(err.get("loc", [])),
            "msg": err.get("msg", ""),
            "type": err.get("type", ""),
        })
    return ORJSONResponse(
        status_code=422,
        content={
            "code": "VALIDATION_ERROR",
            "message": ERROR_CODES["VALIDATION_ERROR"],
            "details": details,
        },
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException,
) -> ORJSONResponse:
    """
    统一的 HTTPException 处理器。
    将 HTTP 状态码映射到内部错误码，返回一致格式的 JSON 响应。
    """
    code_map: dict[int, str] = {
        401: "AUTH_MISSING",
        403: "AUTH_INVALID",
        429: "RATE_LIMIT_EXCEEDED",
        502: "UPSTREAM_CONNECT_ERROR",
        504: "UPSTREAM_TIMEOUT",
    }
    code = code_map.get(exc.status_code, "INTERNAL_ERROR")
    return ORJSONResponse(
        status_code=exc.status_code,
        content={
            "code": code,
            "message": str(exc.detail) if exc.detail else ERROR_CODES.get(code, ""),
        },
    )


async def generic_exception_handler(
    request: Request, exc: Exception,
) -> ORJSONResponse:
    """兜底处理器：未预期异常的最终防线，不泄漏内部错误细节。"""
    return ORJSONResponse(
        status_code=500,
        content={
            "code": "INTERNAL_ERROR",
            "message": ERROR_CODES["INTERNAL_ERROR"],
        },
    )
