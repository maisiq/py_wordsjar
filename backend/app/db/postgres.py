from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

_session_obj: type[AsyncSession] | None = None


def create_sessionmaker(dsn: str, **kwargs: Any):
    global _session_obj

    engine = create_async_engine(
        url=dsn, 
        **kwargs,
    )

    session = async_sessionmaker(engine)

    if _session_obj is not None:
        print("Warning! Reacreating sessionmaker.")
    _session_obj = session


def get_sessionmaker() -> type[AsyncSession]:
    if _session_obj is None:
        raise RuntimeError("sessionmaker is not initialized")
    return _session_obj
