from core.errors import AlreadyExistsError
from models.domain import User
from models.mappers import user_orm_to_domain
from models.orm import UserORM
from psycopg.errors import UniqueViolation
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


class UserRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, user: User) -> None:
        obj = UserORM(
            username=user.username,
            hashed_password=user.hashed_password,
        )
        self._session.add(obj)
        try:
            await self._session.commit()
        except (UniqueViolation, IntegrityError) as e:
            await self._session.rollback()
            raise AlreadyExistsError("user already exists") from e

    async def get(self, username: str) -> User | None:
        query = select(UserORM).where(UserORM.username == username)
        res = await self._session.execute(query)
        user = res.scalar_one_or_none()
        return user_orm_to_domain(user)

    async def get_by_id(self, user_id: int) -> User | None:
        query = select(UserORM).where(UserORM.id == user_id)
        res = await self._session.execute(query)
        user = res.scalar_one_or_none()
        return user_orm_to_domain(user)
