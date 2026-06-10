import datetime as dt
from logging import Logger
from typing import Protocol

from core.errors import InternalError, NotFound
from models.domain import TestWord, UserWord, Word
from repository.params import QueryParams

SUCCESS_POINTS = 0.5
FAILURE_POINTS = 0.25
MAX_RATING = 5.0
MIN_RATING = 0


class Repository(Protocol):
    async def get_word_by_id(self, word_id: str) -> Word | None: ...
    async def get_user_word(self, word_id: str, username: str) -> UserWord | None: ...
    async def update_user_word(self, user_word: UserWord) -> None: ...
    async def words(self, username: str, params: QueryParams) -> list[Word]: ...
    async def test_words(self, username: str, params: QueryParams) -> list[Word]: ...


class ExamService:
    def __init__(self, log: Logger, repo: Repository):
        self._log = log
        self._repo = repo
    
    async def test_words(self, username: str, params: QueryParams) -> list[TestWord]:
        try:
            words = await self._repo.test_words(username, params)
        except Exception as e:
            self._log.error("failed to get test words for user(%s): %s", username, e)
            raise InternalError("internal error")

        test_words = [None]*len(words)
        for idx, w in enumerate(words):
            tw = TestWord(**w.model_dump())
            if idx % 2 == 0:
                tw.reverse = True
            test_words[idx] = tw
        return test_words
    
    async def verify_word(self, username: str, word_id: int, answer: str, reverse: bool) -> bool:
        try:
            word = await self._repo.get_word_by_id(word_id)
        except Exception as e:
            self._log.error("failed to get word for user(%s): %s", username, e)
            raise InternalError("internal error")

        if word is None:
            raise NotFound(f"Word with id:{word_id} doesn't exist")

        answer = answer.lower().strip()

        result = False
        if reverse:
            if word.en == answer:
                result = True
        else:
            for t in word.ru:
                if t == answer:
                    result = True
                    break

        try:
            user_word = await self._repo.get_user_word(word.id, username)
        except Exception as e:
            self._log.error("failed to get user word for user(%s): %s", username, e)
            raise InternalError("internal error")

        if result:
            new_rating = user_word.rating + SUCCESS_POINTS*(user_word.attempts or 1)
            if new_rating > MAX_RATING:
                user_word.rating = MAX_RATING
            else:
                user_word.rating = new_rating
            user_word.attempts += 1
        else:
            new_rating = user_word.rating - FAILURE_POINTS
            if new_rating < MIN_RATING:
                user_word.rating = MIN_RATING
            else:
                user_word.rating = new_rating
            user_word.attempts = 1
        
        user_word.last_attempt = dt.datetime.now(dt.UTC)
        try:
            await self._repo.update_user_word(user_word)
        except Exception as e:
            self._log.error("failed to update user word for user(%s): %s", username, e)
            raise InternalError("internal error")
        return result
