from logging import Logger
from typing import Protocol

from core.errors import AppError, InternalError, NotDue, NotFound
from models.domain import TestWord, UserWord, Word
from repository.params import QueryParams

from .helpers import normalize_word


class Repository(Protocol):
    async def get_word_by_id(self, word_id: int) -> Word | None: ...
    async def get_user_word(self, word_id: int, username: str) -> UserWord | None: ...
    async def apply_answer(
        self, username: str, word_id: int, *, correct: bool
    ) -> tuple[float, int] | None: ...
    async def test_words(self, username: str, params: QueryParams) -> list[TestWord]: ...


class ExamService:
    def __init__(self, log: Logger, repo: Repository):
        self._log = log
        self._repo = repo

    async def test_words(self, username: str, params: QueryParams) -> list[TestWord]:
        try:
            words = await self._repo.test_words(username, params)
        except AppError:
            raise
        except Exception as e:
            self._log.error("failed to get test words for user(%s): %s", username, e)
            raise InternalError("failed to get the exam queue")

        test_words = [None]*len(words)
        for idx, w in enumerate(words):
            tw = TestWord(**w.model_dump())
            if idx % 2 == 0:
                tw.reverse = True
            test_words[idx] = tw
        return test_words

    async def verify_word(self, username: str, word_id: int, answer: str, reverse: bool) -> bool:
        """Check an answer and record it.

        A word that is not in the user's jar is a 404 and a word that was
        answered less than a day ago is a 409: both used to surface as an
        ``AttributeError`` on ``None`` and an unconditional rating bump.
        """
        try:
            word = await self._repo.get_word_by_id(word_id)
        except AppError:
            raise
        except Exception as e:
            self._log.error("failed to get word(%s) for user(%s): %s", word_id, username, e)
            raise InternalError("failed to get the word")

        if word is None:
            raise NotFound(f"word with id {word_id} does not exist")

        correct = self._is_correct(word, answer, reverse)

        try:
            updated = await self._repo.apply_answer(username, word_id, correct=correct)
        except AppError:
            raise
        except Exception as e:
            self._log.error("failed to record the answer of user(%s): %s", username, e)
            raise InternalError("failed to record the answer")

        if updated is None:
            user_word = await self._get_user_word(word_id, username)
            if user_word is None:
                raise NotFound(f"word with id {word_id} is not in the jar")
            raise NotDue("this word was answered recently, it is not due yet")

        return correct

    @staticmethod
    def _is_correct(word: Word, answer: str, reverse: bool) -> bool:
        answer = normalize_word(answer)

        if reverse:
            return normalize_word(word.en) == answer

        # "ё" and "е" are interchangeable in Russian input.
        target = answer.replace("ё", "е")
        return any(translation.replace("ё", "е") == target for translation in word.ru)

    async def _get_user_word(self, word_id: int, username: str) -> UserWord | None:
        try:
            return await self._repo.get_user_word(word_id, username)
        except AppError:
            raise
        except Exception as e:
            self._log.error("failed to get user word for user(%s): %s", username, e)
            raise InternalError("failed to get the word")
