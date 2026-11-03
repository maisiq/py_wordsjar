"""Request id and access logging.

The middleware hands every request a stable identifier (taken from the
``X-Request-ID`` header when a proxy already set one), stores it in a context
variable so that log records can pick it up, echoes it back to the client and
writes a single access log line with the status and the duration.
"""

import time
import uuid

from fastapi import Request
from logger import get_logger, get_request_id, reset_request_id, set_request_id
from starlette.responses import Response

REQUEST_ID_HEADER = "X-Request-ID"

#: Long client supplied ids are ignored: they end up in every log line.
MAX_REQUEST_ID_LENGTH = 64


def _request_id_from(request: Request) -> str:
    incoming = request.headers.get(REQUEST_ID_HEADER, "").strip()
    if incoming and len(incoming) <= MAX_REQUEST_ID_LENGTH:
        return incoming
    return uuid.uuid4().hex


def client_ip(request: Request) -> str:
    # nginx sets X-Real-IP; X-Forwarded-For is kept for the direct case.
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else "unknown"


async def request_context_middleware(request: Request, call_next) -> Response:
    token = set_request_id(_request_id_from(request))
    started = time.perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        # The dedicated error middleware turns this into a response; log the
        # access line here so a failed request is still accounted for.
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        get_logger().error(
            "request failed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status": 500,
                "duration_ms": duration_ms,
                "client": client_ip(request),
            },
        )
        reset_request_id(token)
        raise

    duration_ms = round((time.perf_counter() - started) * 1000, 2)
    response.headers[REQUEST_ID_HEADER] = get_request_id()

    get_logger().info(
        "request",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": duration_ms,
            "client": client_ip(request),
        },
    )

    reset_request_id(token)
    return response