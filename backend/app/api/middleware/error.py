"""Last-resort error handling.

Domain errors are translated by the exception handlers registered in
``api.errors``. This middleware only catches what escaped them, logs it with a
full traceback and returns a generic body that carries the request id, so a
report from a user can be matched to a log line.
"""

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from logger import get_logger, get_request_id


async def error_logger_middleware(request: Request, call_next):
    log = get_logger()

    try:
        return await call_next(request)
    except HTTPException:
        raise
    except Exception:
        log.exception(
            "unhandled error while processing %s %s",
            request.method,
            request.url.path,
        )
        return JSONResponse(
            {
                "detail": "internal error",
                "code": "internal_error",
                "request_id": get_request_id(),
            },
            status_code=500,
        )