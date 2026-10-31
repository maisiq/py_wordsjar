from logging import Logger
from typing import Protocol

from core.errors import AppError, InternalError
from models.domain import Status, Word
from repository.params import QueryParams

from .helpers import normalize_word


class Repository(Protocol):
    async def add_words(self, username: str, words: list[str], rating: float) -> int: ...
    async def words(self, username: str, params: QueryParams) -> list[Word]: ...
    async def delete(self, username: str, word: str) -> int: ...


#: Starting rating for a word, based on what the user said about it.
STATUS_RATING = {
    Status.NEW: 0.0,
    Status.MEDIUM: 2.5,
    Status.WELLKNOWN: 5.0,
}


class JarService:
    def __init__(self, log: Logger, repo: Repository):
        self._log = log
        self._repo = repo

    async def words(self, username: str, params: QueryParams) -> list[Word]:
        try:
            return await self._repo.words(username, params)
        except AppError:
            raise
        except AppError:
            raise
        except Exception as e:
            self._log.error("failed to get word list: %s | error_type: %s", e, type(e))
            raise InternalError()

    async def add_words(self, username: str, words: list[str], status: Status | None) -> int:
        rating = STATUS_RATING[status or Status.NEW]
        # Words are stored normalised, so the lookup has to normalise as well:
        # "Apple" used to be reported as a word that does not exist.
        normalised = [normalize_word(word) for word in words]

        try:
            return await self._repo.add_words(username, normalised, rating)
        except AppError:
            raise
        except Exception as e:
            self._log.error("failed to add word (%s) to jar: %s | error_type: %s", words, e, type(e))
            raise InternalError()

    async def delete_word(self, username: str, word: str) -> int:
        try:
            return await self._repo.delete(username, normalize_word(word))
        except AppError:
            raise
        except Exception as e:
            self._log.error("failed to delete word (%s) from jar: %s | error_type: %s", word, e, type(e))
            raise InternalError()