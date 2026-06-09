"""全局异常处理器"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from .schemas.error import ERROR_CODES


def register_exception_handlers(app: FastAPI) -> None:
    """注册所有全局异常处理器"""

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        status_code, error_type = ERROR_CODES["VALIDATION_ERROR"]
        return JSONResponse(
            status_code=status_code,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": str(exc.errors()),
                    "type": error_type,
                }
            },
        )

    @app.exception_handler(HTTPException)
    async def http_handler(request: Request, exc: HTTPException):
        detail = exc.detail
        if isinstance(detail, dict) and "code" in detail:
            code = detail["code"]
            message = detail.get("message", str(detail))
        else:
            code = "UNKNOWN"
            message = str(detail)

        status_code, error_type = ERROR_CODES.get(
            code, (exc.status_code, "api_error")
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": code,
                    "message": message,
                    "type": error_type if isinstance(error_type, str) else error_type[1],
                }
            },
        )

    @app.exception_handler(Exception)
    async def general_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": str(exc),
                    "type": "server_error",
                }
            },
        )
