from collections.abc import Mapping
from typing import ClassVar

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    status_code = 500
    headers: ClassVar[Mapping[str, str] | None] = None

    def __init__(self, detail: str | list[str]) -> None:
        super().__init__(str(detail))
        self.detail = detail


class UnauthorizedError(AppError):
    status_code = 401
    headers: ClassVar[Mapping[str, str] | None] = {"WWW-Authenticate": "Bearer"}


class NotFoundError(AppError):
    status_code = 404


class ConflictError(AppError):
    status_code = 409


class PayloadTooLargeError(AppError):
    status_code = 413


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=exc.headers,
        )
