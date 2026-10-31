from logging import Logger
from typing import Protocol

from core.errors import AlreadyExistsError, AppError, InternalError, NotFound
from models.domain import Word
from repository.params import QueryParams

from .helpers import normalize_word


class Repository(Protocol):
    async def get_word(self, word: str) -> Word: ...
    async def add_word(self, word: Word) -> None: ...
    async def words(self, params: QueryParams) -> list[Word]: ...
    async def get_words_start_with(self, query: str, limit: int, user: str | None = None) -> list[Word]: ...


class WordService:
    def __init__(self, log: Logger, repo: Repository):
        self._log = log
        self._repo = repo

    async def get_word(self, word: str) -> Word:
        try:
            return await self._repo.get_word(normalize_word(word))
        except AppError:
            raise
        except Exception as e:
            self._log.error("failed to get word (%s): %s", word, e)
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
            raise InternalError("failed to add the word")

    async def words(self, params: QueryParams) -> list[Word]:
        try:
            return await self._repo.words(params)
        except AppError:
            raise
        except Exception as e:
            self._log.error("failed to get word list: %s | error_type: %s", e, type(e))
            raise InternalError("failed to get the word list")

    async def search(self, query: str, limit: int, user: str | None = None) -> list[Word]:
        query = query.strip().lower()
        try:
            return await self._repo.get_words_start_with(query, limit, user)
        except AppError:
            raise
        except Exception as e:
            self._log.error("failed to get words by search query(%s): %s", query, e)
            raise InternalError("failed to search words")