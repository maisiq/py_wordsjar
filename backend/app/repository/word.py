from core.errors import AlreadyExistsError, NotFound
from models.mappers import word_orm_to_domain
from models.orm import UserORM, UserWordORM, WordORM
from psycopg.errors import UniqueViolation
from repository.params import QueryParams
from services.words import Word
from sqlalchemy import and_, literal, select, tuple_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


class WordRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_word(self, word: str) -> Word:
        q = select(WordORM).where(WordORM.en == word)
        res = await self._session.execute(q)
        word_obj = res.scalar_one_or_none()
        if word_obj is None:
            raise NotFound(f"word '{word}' not found")

        return word_orm_to_domain(word_obj)

    async def add_word(self, word: Word) -> None:
        w = WordORM(
            en=word.en,
            ru=word.ru,
            transcription=word.transcription,
            examples=word.examples,
        )

        self._session.add(w)
        try:
            await self._session.commit()
        except (UniqueViolation, IntegrityError):
            raise AlreadyExistsError("word already exists")

    async def words(self, params: QueryParams) -> list[Word]: 
        order_fields = []
        for f in params.sort_by:
            field = getattr(WordORM, f, None) or getattr(UserWordORM, f, None)

            if field is not None:
                order_fields.append(field)

        order_by = [
            f.desc() if params.desc else f.asc()
            for f in order_fields
        ]

        if params.username:
            user_id_subq = select(UserORM.id).where(UserORM.username == params.username).scalar_subquery()
            query = (
                select(WordORM, (UserWordORM.user_id.is_not(None)).label("in_jar"))
                .outerjoin(
                    UserWordORM, 
                    and_(
                        UserWordORM.word_id == WordORM.id,
                        UserWordORM.user_id == user_id_subq,
                    )
                )
            )
        else:
            query = select(WordORM, literal(False).label("in_jar"))

        query = query.limit(params.limit).order_by(*order_by)

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
        word_objs = res.tuples().all()

        words: list[Word] = [None]*len(word_objs)
        for idx, word_and_status in enumerate(word_objs):
            w, status = word_and_status
            word = word_orm_to_domain(w)
            word.in_jar = status
            words[idx] = word
        return words

    async def get_words_start_with(self, query: str, limit: int, user: str | None = None) -> list[Word]:
        if user:
            user_id_subq = select(UserORM.id).where(UserORM.username == user).scalar_subquery()
            q = (
                select(WordORM, (UserWordORM.user_id.is_not(None)).label("in_jar"))
                .outerjoin(
                    UserWordORM, 
                    and_(
                        UserWordORM.word_id == WordORM.id,
                        UserWordORM.user_id == user_id_subq,
                    )
                )
            )
        else:
            q = select(WordORM, literal(False).label("in_jar"))

        q = q.where(WordORM.en.startswith(query)).limit(limit)

        res = await self._session.execute(q)
        word_objs = res.tuples().all()

        words: list[Word] = [None]*len(word_objs)
        for idx, word_and_status in enumerate(word_objs):
            w, status = word_and_status
            word = word_orm_to_domain(w)
            word.in_jar = status
            words[idx] = word
        return words
