from .domain import User, Word
from .orm import UserORM, WordORM


def word_orm_to_domain(w: WordORM) -> Word:
    return Word(
        id=w.id,
        en=w.en,
        ru=w.ru,
        transcription=w.transcription,
        examples=w.examples,
    )

def user_orm_to_domain(u: UserORM) -> User:
    return User(
        id=u.id,
        hashed_password=u.hashed_password,
        username=u.username,
        role=u.role,
    )
