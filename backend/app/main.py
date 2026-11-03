import contextlib

import logger
from api.errors import register_error_handlers
from api.middleware.error import error_logger_middleware
from api.middleware.request import REQUEST_ID_HEADER, request_context_middleware
from api.v1.router import router as api_router
from api.v1.routes.health import router as health_router
from core import config
from db import postgres
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from logger import get_logger


def init() -> FastAPI:
    settings = config.init()
    app_settings = settings.app
    cors_settings = settings.cors

    logger.init(app_settings.debug, json_logs=not app_settings.debug)
    log = get_logger()

    # Fail at startup, not on the first sign-in: a missing or too short signing
    # key makes every authenticated endpoint unusable.
    settings.jwt.read_signing_key()

    if cors_settings.dropped_origins:
        log.warning(
            "ignoring invalid CORS origins (they must include a scheme)",
            extra={"dropped_origins": cors_settings.dropped_origins},
        )
    if "*" in cors_settings.origins and cors_settings.allow_credentials:
        log.warning("wildcard CORS origin cannot be combined with credentials")

    postgres.init(settings.db)

    @contextlib.asynccontextmanager
    async def lifespan(_: FastAPI):
        log.info(
            "application started",
            extra={
                "environment": app_settings.environment,
                "debug": app_settings.debug,
                "docs": app_settings.docs,
                "cors_origins": cors_settings.origins,
                "pool": postgres.pool_status(),
            },
        )
        try:
            yield
        finally:
            await postgres.dispose()
            log.info("application stopped")

    app = FastAPI(
        title="wordsjar",
        version="0.1.0",
        debug=app_settings.debug,
        lifespan=lifespan,
        docs_url="/docs" if app_settings.docs else None,
        redoc_url=None,
        openapi_url="/openapi.json" if app_settings.docs else None,
    )

    # add_middleware prepends, so the middleware added last runs first. The
    # resulting order is: request id -> CORS -> error handling -> routing.
    # Keeping CORS outside the error handling is what makes 500 responses
    # readable by a browser on another origin.
    app.middleware("http")(error_logger_middleware)
    if cors_settings.origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_settings.origins,
            allow_credentials=cors_settings.allow_credentials,
            allow_methods=cors_settings.allow_methods,
            allow_headers=cors_settings.allow_headers,
            expose_headers=[REQUEST_ID_HEADER],
        )
    app.middleware("http")(request_context_middleware)

    app.include_router(health_router)
    app.include_router(api_router)

    register_error_handlers(app)

    return app