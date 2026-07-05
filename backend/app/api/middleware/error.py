from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from logger import get_logger


async def error_logger_middleware(request: Request, call_next):
    log = get_logger()

    try:
        response = await call_next(request)
        return response
    except HTTPException:
        raise
    except Exception as e:
        log.exception("failed to process response: %s", e)
        return JSONResponse({"detail": "internal error"}, status.HTTP_500_INTERNAL_SERVER_ERROR)
