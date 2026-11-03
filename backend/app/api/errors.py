"""Exception handlers: the single place where errors become HTTP responses.

The body keeps the ``detail`` key because the frontend translates it, and adds a
stable ``code`` (for the client to branch on) plus the ``request_id`` that also
appears in the logs.
"""

from core import errors
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from logger import get_logger, get_request_id
from starlette.exceptions import HTTPException as StarletteHTTPException


def _payload(detail: str, code: str, extra: dict | None = None) -> dict:
    body = {"detail": detail, "code": code, "request_id": get_request_id()}
    if extra:
        body.update(extra)
    return body


def register_error_handlers(app: FastAPI) -> None:
    log = get_logger()

    @app.exception_handler(errors.AppError)
    async def handle_app_error(request: Request, exc: errors.AppError) -> JSONResponse:
        headers: dict[str, str] = {}
        if isinstance(exc, errors.RateLimited):
            headers["Retry-After"] = str(exc.retry_after)

        if exc.status_code >= 500:
            log.error(
                "request failed: %s",
                exc.message,
                extra={"method": request.method, "path": request.url.path, "status": exc.status_code},
            )
        else:
            log.info(
                "request rejected: %s",
                exc.message,
                extra={"method": request.method, "path": request.url.path, "status": exc.status_code},
            )

        return JSONResponse(
            _payload(exc.message, exc.code),
            status_code=exc.status_code,
            headers=headers or None,
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        detail = exc.detail if isinstance(exc.detail, str) else "request failed"
        return JSONResponse(
            _payload(detail, f"http_{exc.status_code}"),
            status_code=exc.status_code,
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        # FastAPI's default body is a list of objects that no UI can display;
        # keep the machine readable part under a separate key.
        fields = []
        for error in exc.errors():
            location = ".".join(str(part) for part in error.get("loc", ()))
            fields.append({"field": location, "message": error.get("msg", "")})

        return JSONResponse(
            _payload("invalid request", "validation_error", {"errors": fields}),
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
