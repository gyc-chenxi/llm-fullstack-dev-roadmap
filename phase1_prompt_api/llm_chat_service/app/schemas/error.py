"""统一错误响应格式"""

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    code: str = Field(..., description="错误码")
    message: str = Field(..., description="错误描述")
    type: str = Field(default="api_error", description="错误类型")


class ErrorResponse(BaseModel):
    error: ErrorDetail


# 预设错误码
ERROR_CODES = {
    "VALIDATION_ERROR": (422, "invalid_request_error"),
    "AUTH_MISSING": (401, "authentication_error"),
    "AUTH_INVALID": (403, "authentication_error"),
    "RATE_LIMIT_EXCEEDED": (429, "rate_limit_error"),
    "MODEL_NOT_FOUND": (404, "invalid_request_error"),
    "UPSTREAM_TIMEOUT": (504, "server_error"),
    "UPSTREAM_ERROR": (502, "server_error"),
    "INTERNAL_ERROR": (500, "server_error"),
}
