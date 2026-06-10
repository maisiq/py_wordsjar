import datetime as dt

from core.errors import AlreadyExistsError
from models.domain import UserWord, Word
from models.mappers import word_orm_to_domain
from models.orm import UserORM, UserWordORM, WordORM
from repository.params import QueryParams
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


class JarRepository:
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def add_word(self, username: str, word: str, rating: float):
        res = await self._session.execute(
            select(UserORM.id)
            .where(UserORM.username == username)
        )
        user_id = res.scalar_one_or_none()
        if user_id is None:
            raise Exception("user not exists")

        res = await self._session.execute(select(WordORM.id).where(WordORM.en == word))
        word_id = res.scalar_one_or_none()
        if word_id is None:
            raise Exception("word not exists")

        stmt = (
            insert(UserWordORM)
            .values(
                user_id=user_id,
                word_id=word_id,
                rating=rating,
                last_attempt=dt.datetime.now(dt.UTC) - dt.timedelta(days=1),
            )
            .on_conflict_do_nothing(index_elements=["user_id", "word_id"])
        )

        try:
            await self._session.execute(stmt)
            await self._session.commit()
        except IntegrityError as e:
            raise AlreadyExistsError("word already added to jar")

    async def get_word_by_id(self, word_id: str) -> Word | None:
        query = select(WordORM).where(WordORM.id == word_id)
        res = await self._session.execute(query)
        word_orm = res.scalar_one_or_none()
        if word_orm is None:
            return
        return word_orm_to_domain(word_orm)

    async def get_user_word(self, word_id: int, username: str) -> UserWord | None:
        stmt = (
            select(UserWordORM)
            .join(UserWordORM.user)
            .where(
                UserWordORM.word_id == word_id,
                UserORM.username == username,
            )
        )

        res = await self._session.execute(stmt)
        uw = res.scalar_one_or_none()

        if uw is None:
            return

        user_word = UserWord(
            word_id=uw.word_id,
            username=username,
            rating=uw.rating,
            attempts=uw.attempts,
            last_attempt=uw.last_attempt,
        )
        return user_word

    async def update_user_word(self, uw: UserWord) -> None:
        res = await self._session.execute(
            select(UserORM.id).where(UserORM.username == uw.username)
        )
        user_id = res.scalar_one()

        stmt = (
            update(UserWordORM)
            .where(UserWordORM.user_id == user_id, UserWordORM.word_id == uw.word_id)
            .values(
                rating=uw.rating,
                attempts=uw.attempts,
                last_attempt=uw.last_attempt,
            )
        )

        await self._session.execute(stmt)
        await self._session.commit()

    async def test_words(self, username: str, params: QueryParams) -> list[Word]:
        query = (
            select(WordORM)
            .join(UserWordORM, WordORM.id == UserWordORM.word_id)
            .join(UserORM, UserORM.id == UserWordORM.user_id)
            .where(UserORM.username == username)
            .limit(params.limit)
        )

        ts = dt.datetime.now() - dt.timedelta(days=1)

        query = query.where(
            UserWordORM.rating < 5.0, 
            UserWordORM.last_attempt < ts,
        ).order_by(UserWordORM.rating, UserWordORM.last_attempt)
        
        res = await self._session.execute(query)
        words_orm = res.scalars().all()

        words: list[WordORM] = [None]*len(words_orm)
        for i, word in enumerate(words_orm):
            words[i] = word_orm_to_domain(word)
        return words


    async def words(self, username: str, params: QueryParams) -> list[Word]:
        query = (
            select(WordORM)
            .join(UserWordORM, WordORM.id == UserWordORM.word_id)
            .join(UserORM, UserORM.id == UserWordORM.user_id)
            .where(UserORM.username == username)
            .limit(params.limit)
        )

        order_by_field = getattr(WordORM, params.sort_by)
        order_by = order_by_field.desc() if params.desc else order_by_field.asc()
        query = query.order_by(order_by)

        if params.pointer:
            if params.desc:
                query = query.where(order_by_field < params.pointer)
            else:
                query = query.where(order_by_field > params.pointer)

        res = await self._session.execute(query)
        words_orm = res.scalars().all()

        words = [None]*len(words_orm)
        for i, word in enumerate(words_orm):
            words[i] = word_orm_to_domain(word)
        return words
