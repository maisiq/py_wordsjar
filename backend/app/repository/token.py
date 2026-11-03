"""Server side token storage.

The previous implementation kept refresh tokens in a process local ``TTLCache``:
every restart logged everybody out, a second worker had its own copy, the
``ttl`` argument was ignored and the 256 entry cap silently evicted live
sessions. Sessions are rows in ``auth_session`` now, so they survive restarts,
are shared between workers and can be revoked reliably.
"""

import datetime as dt
from hashlib import sha256

from models.orm import AuthSessionORM
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

REFRESH = "refresh"
ACCESS = "access"


def token_hash(token: str) -> str:
    return sha256(token.encode("utf8")).hexdigest()


class TokenStorage:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def store(
        self,
        token: str,
        *,
        user_id: int,
        ttl: int,
        kind: str = REFRESH,
    ) -> None:
        """Remember a token until ``ttl`` seconds from now."""
        expires_at = dt.datetime.now(dt.UTC) + dt.timedelta(seconds=max(1, ttl))

        stmt = (
            insert(AuthSessionORM)
            .values(
                token_hash=token_hash(token),
                kind=kind,
                user_id=user_id,
                expires_at=expires_at,
            )
            .on_conflict_do_nothing(index_elements=["token_hash"])
        )
        await self._session.execute(stmt)
        await self._session.commit()

    async def consume(self, token: str, kind: str = REFRESH) -> int | None:
        """Delete the token and return its owner in one statement.

        ``DELETE ... RETURNING`` makes refresh rotation safe: of two parallel
        requests carrying the same refresh token exactly one receives the row,
        the other one is rejected instead of minting a second session.
        """
        stmt = (
            delete(AuthSessionORM)
            .where(
                AuthSessionORM.token_hash == token_hash(token),
                AuthSessionORM.kind == kind,
            )
            .returning(AuthSessionORM.user_id)
        )
        result = await self._session.execute(stmt)
        user_id = result.scalar_one_or_none()
        await self._session.commit()
        return user_id

    async def is_revoked(self, token: str, kind: str = ACCESS) -> bool:
        stmt = (
            select(AuthSessionORM.token_hash)
            .where(
                AuthSessionORM.token_hash == token_hash(token),
                AuthSessionORM.kind == kind,
                AuthSessionORM.expires_at > dt.datetime.now(dt.UTC),
            )
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def delete_for_user(self, user_id: int, kind: str | None = None) -> int:
        """Revoke every session of a user (password change, "log out everywhere")."""
        stmt = delete(AuthSessionORM).where(AuthSessionORM.user_id == user_id)
        if kind is not None:
            stmt = stmt.where(AuthSessionORM.kind == kind)
        result = await self._session.execute(stmt)
        await self._session.commit()
        return result.rowcount or 0

    async def cleanup_expired(self) -> int:
        """Drop expired rows; called on startup so the table cannot grow forever."""
        stmt = delete(AuthSessionORM).where(AuthSessionORM.expires_at <= dt.datetime.now(dt.UTC))
        result = await self._session.execute(stmt)
        await self._session.commit()
        return result.rowcount or 0