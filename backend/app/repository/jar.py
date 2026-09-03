import datetime as dt

from models.domain import JarWord, UserWord, Word
from models.mappers import create_jar_word, word_orm_to_domain
from models.orm import UserORM, UserWordORM, WordORM
from repository.params import QueryParams
from sqlalchemy import delete, select, tuple_, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession


class JarRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add_words(self, username: str, words: list[str], rating: float):
        res = await self._session.execute(
            select(UserORM.id)
            .where(UserORM.username == username)
        )
        user_id = res.scalar_one_or_none()
        if user_id is None:
            raise Exception("user not exists")

        res = await self._session.execute(select(WordORM.id).where(WordORM.en.in_(words)))
        word_ids = res.scalars().all()
        if not word_ids:
            raise Exception("word not exists")

        last_attempt = dt.datetime.now(dt.UTC) - dt.timedelta(days=1)

        data_to_insert = [None]*len(word_ids)
        for idx, word_id in enumerate(word_ids):
            data_to_insert[idx] = {
                "user_id": user_id,
                "word_id": word_id,
                "rating": rating,
                "last_attempt": last_attempt,
            }

        stmt = (
            insert(UserWordORM)
            .on_conflict_do_nothing(index_elements=["user_id", "word_id"])
            .returning(UserWordORM.word_id)
        )

        res = await self._session.execute(stmt, data_to_insert)
        await self._session.commit()

        inserted_rows = res.all()
        return len(inserted_rows)

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
            UserWordORM.rating <= 5.0,
            UserWordORM.last_attempt < ts,
        ).order_by(UserWordORM.rating, UserWordORM.last_attempt)

        res = await self._session.execute(query)
        words_orm = res.scalars().all()

        words: list[WordORM] = [None]*len(words_orm)
        for i, word in enumerate(words_orm):
            words[i] = word_orm_to_domain(word)
        return words

    async def words(self, username: str, params: QueryParams) -> list[JarWord]:
        query = (
            select(WordORM, UserWordORM.rating)
            .join(UserWordORM, WordORM.id == UserWordORM.word_id)
            .join(UserORM, UserORM.id == UserWordORM.user_id)
            .where(UserORM.username == username)
            .limit(params.limit)
        )

        order_fields = []
        for f in params.sort_by:
            field = getattr(WordORM, f, None) or getattr(UserWordORM, f, None)

            if field is not None:
                order_fields.append(field)

        order_by = [
            f.desc() if params.desc else f.asc()
            for f in order_fields
        ]

        query = query.order_by(*order_by)

        if params.pointer:
            values = []
            for idx, field in enumerate(order_fields):
                factory = field.expression.type.python_type
                value = factory(params.pointer[idx])
                values.append(value)

            if params.desc:
                query = query.where(tuple_(*order_fields) < values)
            else:
                query = query.where(tuple_(*order_fields) > values)

        res = await self._session.execute(query)
        words_orm = res.tuples().all()

        words = [None]*len(words_orm)
        for i, (word, rating) in enumerate(words_orm):
            words[i] = create_jar_word(word, rating)
        return words

    async def delete(self, username: str, word: str) -> None:
        stmt = (
            delete(UserWordORM)
            .where(
                UserWordORM.user.has(UserORM.username == username),
                UserWordORM.word.has(WordORM.en == word),
            )
        )
        await self._session.execute(stmt)
        await self._session.commit()
