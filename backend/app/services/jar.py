from enum import StrEnum
from logging import Logger
from typing import Protocol

from core.errors import AlreadyExistsError, InternalError
from models.domain import Word
from repository.params import QueryParams


class Repository(Protocol):
    async def add_word(self, username: str, word: str, rating: float): ...
    async def words(self, username: str, params: QueryParams) -> list[Word]: ...


class Status(StrEnum):
    NEW = "new"
    MEDIUM = "medium"
    WELLKNOWN = "wellknown"


class JarService:
    def __init__(self, log: Logger, repo: Repository):
        self._log = log
        self._repo = repo
    
    async def words(self, username: str, params: QueryParams) -> list[Word]:
        try:
            return await self._repo.words(username, params)
        except Exception as e:
            self._log.error("failed to get word list: %s | error_type: %s", e, type(e))
            raise InternalError()

    async def add_word(self, username: str, word: str, status: Status):
        match status:
            case Status.MEDIUM:
                rating = 2.5
            case Status.WELLKNOWN:
                rating = 5.0
            case _:
                rating = 0.0
        try:
            await self._repo.add_word(username, word, rating)
        except AlreadyExistsError:
            raise
        except Exception as e:
            self._log.error("failed to add word (%s) to jar: %s | error_type: %s", word, e, type(e))
            raise InternalError()
