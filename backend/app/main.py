import logger
from api.v1.router import router
from core import config
from db.postgres import create_sessionmaker
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def init():
    config.init()
    app_settings = config.get_app_settings()
    db_settings = config.get_db_settings()
    cors_settings = config.get_cors_settings()

    logger.init(app_settings.debug)
    log = logger.get_logger()

    app = FastAPI(
        debug=app_settings.debug,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_settings.origins,
        allow_credentials=cors_settings.allow_credentials,
        allow_methods=cors_settings.allow_methods,
        allow_headers=cors_settings.allow_headers,
    )

    log.info("Creating connection pool to db")
    create_sessionmaker(db_settings.dsn, echo=app_settings.debug)

    app.include_router(router)

    return app
