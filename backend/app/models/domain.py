import datetime as dt
from enum import StrEnum
from typing import ClassVar

from pydantic import BaseModel, Field


class Word(BaseModel):
    id: int | None = None
    en: str
    ru: list[str]
    transcription: str
    examples: list[str] | None = Field(default_factory=list)

    valid_sort_fields: ClassVar[tuple[str]] = ("en", "id")

    @classmethod
    def is_valid_sort_field(cls, field: str) -> bool:
        return field in cls.valid_sort_fields


class TestWord(Word):
    reverse: bool = False


class UserWord(BaseModel):
    word_id: int
    username: str
    rating: float
    attempts: int
    last_attempt: dt.datetime


class User(BaseModel):
    id: int | None = None
    username: str
    role: str
    hashed_password: str


class Tokens(BaseModel):
    username: str | None = None
    access: str | None = None
    refresh: str | None = None


class UserInfo(BaseModel):
    username: str
    role: str


class Roles(StrEnum):
    USER = "user"
    ADMIN = "admin"