from .domain import JarWord, TestWord, User, Word
from .orm import UserORM, WordORM


def word_orm_to_domain(w: WordORM) -> Word:
    return Word(
        id=w.id,
        en=w.en,
        ru=w.ru,
        transcription=w.transcription,
        examples=w.examples,
    )


def user_orm_to_domain(u: UserORM | None) -> User | None:
    if u is None:
        return None

    return User(
        id=u.id,
        hashed_password=u.hashed_password,
        username=u.username,
        role=u.role,
    )


def create_jar_word(w: WordORM, rating: float) -> JarWord:
    return JarWord(
        id=w.id,
        en=w.en,
        ru=w.ru,
        transcription=w.transcription,
        examples=w.examples,
        rating=rating,
        # Everything the jar lists is, by definition, in the jar.
        in_jar=True,
    )


def create_test_word(w: WordORM, rating: float, last_attempt) -> TestWord:
    return TestWord(
        id=w.id,
        en=w.en,
        ru=w.ru,
        transcription=w.transcription,
        examples=w.examples,
        rating=rating,
        last_attempt=last_attempt,
        in_jar=True,
    )