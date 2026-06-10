from core.errors import AlreadyExistsError, NotFound
from models.orm import WordORM
from psycopg.errors import UniqueViolation
from repository.params import QueryParams
from services.words import Word
from sqlalchemy import select
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

        return Word(
            id=word_obj.id,
            en=word_obj.en, 
            ru=word_obj.ru, 
            transcription=word_obj.transcription,
            examples=word_obj.examples,
        )

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
        except (UniqueViolation, IntegrityError) as e:
            raise AlreadyExistsError("word already exists")

    async def words(self, params: QueryParams) -> list[Word]: 
        order_by_field = getattr(WordORM, params.sort_by)
        order_by = order_by_field.desc() if params.desc else order_by_field.asc()
        query = select(WordORM).limit(params.limit).order_by(order_by)

        if params.pointer:
            if params.desc:
                query = query.where(order_by_field < params.pointer)
            else:
                query = query.where(order_by_field > params.pointer)

        res = await self._session.execute(query)
        word_objs = res.scalars().all()

        words = [None]*len(word_objs)
        for idx, word in enumerate(word_objs):
            words[idx] = Word(
                id=word.id,
                en=word.en, 
                ru=word.ru, 
                transcription=word.transcription,
                examples=word.examples,
            )
        return words
