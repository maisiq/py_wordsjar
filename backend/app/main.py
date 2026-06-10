import logger
from api.v1.router import router
from core.config import ORIGINS, AppSettings, DatabaseSettings
from db.postgres import create_sessionmaker
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def init():
    app_settings = AppSettings()
    db_settings = DatabaseSettings()

    logger.init(app_settings.debug)
    log = logger.get_logger()

    app = FastAPI(
        debug=app_settings.debug,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    log.info("Creating connection pool to db")
    create_sessionmaker(db_settings.pg_dsn, echo=app_settings.debug)

    app.include_router(router)

    return app
