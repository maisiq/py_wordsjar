from core.errors import AlreadyExistsError, NotFound
from models.mappers import word_orm_to_domain
from models.orm import UserORM, UserWordORM, WordORM
from psycopg.errors import UniqueViolation
from repository.params import QueryParams
from services.words import Word
from sqlalchemy import literal, select
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
        order_by_field = getattr(WordORM, params.sort_by)
        order_by = order_by_field.desc() if params.desc else order_by_field.asc()

        if params.username:
            query = (
                select(WordORM, (UserWordORM.user_id.is_not(None)).label("in_jar"))
                .outerjoin(UserWordORM, UserWordORM.word_id == WordORM.id)
                .outerjoin(UserWordORM.user.and_(UserORM.username == params.username))
            )
        else:
            query = select(WordORM, literal(False).label("in_jar"))

        query = query.limit(params.limit).order_by(order_by)

        if params.pointer:
            if params.desc:
                query = query.where(order_by_field < params.pointer)
            else:
                query = query.where(order_by_field > params.pointer)

        res = await self._session.execute(query)
        word_objs = res.tuples().all()

        words: list[Word] = [None]*len(word_objs)
        for idx, word_and_status in enumerate(word_objs):
            w, status = word_and_status
            word = word_orm_to_domain(w)
            word.in_jar = status
            words[idx] = word
        return words
