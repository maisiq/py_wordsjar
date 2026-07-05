from logging import Logger
from typing import Protocol

from core.errors import AlreadyExistsError, InternalError, NotFound
from models.domain import Word
from repository.params import QueryParams

from .helpers import normalize_word


class Repository(Protocol):
    async def get_word(self, word: str): ...
    async def add_word(self, word: Word): ...
    async def words(self, params: QueryParams) -> list[Word]: ...
    async def get_words_start_with(self, query: str, limit: int) -> list[Word]: ...


class WordService:
    def __init__(self, log: Logger, repo: Repository):
        self._log = log
        self._repo = repo

    async def get_word(self, word: str) -> Word | None:
        try:
            w = await self._repo.get_word(word)
            return w
        except NotFound:
            return
        except Exception as e:
            raise InternalError("failed to get the word")

    async def add_word(self, word: Word) -> None:
        word.en = normalize_word(word.en)
        word.ru = [normalize_word(w) for w in word.ru]

        try:
            await self._repo.add_word(word)
        except AlreadyExistsError:
            raise
        except Exception as e:
            self._log.error("failed to add word (%s) to repo: %s | error_type: %s", word, e, type(e))
            raise InternalError()

    async def words(self, params: QueryParams) -> list[Word]:
        words = await self._repo.words(params)
        return words
    
    async def search(self, query: str, limit: int) -> list[Word]:
        query = query.strip().lower()
        try:
            return await self._repo.get_words_start_with(query, limit)
        except Exception as e:
            self._log.error("failed to get words by search quer(%s): %s", query, e)
            raise InternalError("internal error")
