"""Database engine and session factory.

The engine is created once per process, configured with an explicit pool and
timeouts, and disposed on shutdown (see ``main.init``).
"""

import typing

from core import config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def init(settings: config.DatabaseSettings) -> None:
    global _engine, _sessionmaker

    if _engine is not None:
        raise RuntimeError("database engine is already initialized")

    _engine = create_async_engine(
        url=settings.dsn,
        echo=settings.echo,
        pool_size=settings.pool_size,
        max_overflow=settings.max_overflow,
        pool_timeout=settings.pool_timeout,
        pool_recycle=settings.pool_recycle,
        pool_pre_ping=settings.pool_pre_ping,
        connect_args=settings.connect_args,
    )
    # expire_on_commit=False keeps already loaded attributes usable after a
    # commit without an implicit refresh round-trip.
    _sessionmaker = async_sessionmaker(_engine, expire_on_commit=False)


def get_engine() -> AsyncEngine:
    if _engine is None:
        raise RuntimeError("database engine is not initialized")
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    if _sessionmaker is None:
        raise RuntimeError("sessionmaker is not initialized")
    return _sessionmaker


async def dispose() -> None:
    global _engine, _sessionmaker

    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _sessionmaker = None


async def check_connection() -> None:
    """Ping the database; used by the readiness probe."""
    engine = get_engine()
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))


def pool_status() -> dict[str, typing.Any]:
    """Pool counters for metrics and troubleshooting."""
    if _engine is None:
        return {"initialized": False}
    pool = _engine.pool
    return {
        "initialized": True,
        "size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
    }