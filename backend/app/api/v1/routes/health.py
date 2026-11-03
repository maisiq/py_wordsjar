"""Health and readiness probes.

``/healthz`` answers as long as the process is alive; ``/readyz`` also checks
that the database is reachable, so an orchestrator does not route traffic to an
instance that cannot serve requests.
"""

from db.postgres import check_connection, pool_status
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from logger import get_logger

router = APIRouter(tags=["health"])


@router.get("/healthz", include_in_schema=False)
async def liveness() -> JSONResponse:
    return JSONResponse({"status": "ok"})


@router.get("/readyz", include_in_schema=False)
async def readiness() -> JSONResponse:
    log = get_logger()
    try:
        await check_connection()
    except Exception:
        log.exception("readiness check failed: database is not reachable")
        return JSONResponse(
            {"status": "unavailable", "database": "down"},
            status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    return JSONResponse({"status": "ok", "database": "up", "pool": pool_status()})