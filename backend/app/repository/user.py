from models.domain import User
from models.mappers import user_orm_to_domain
from models.orm import UserORM
from sqlalchemy import select
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
        await self._session.commit()

    async def get(self, username: str) -> User | None:
        query = select(UserORM).where(UserORM.username == username)
        res = await self._session.execute(query)
        user = res.scalar_one_or_none()
        return user_orm_to_domain(user)

