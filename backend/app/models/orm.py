from datetime import datetime

from sqlalchemy import (
    ARRAY,
    DateTime,
    Float,
    ForeignKey,
    Identity,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    type_annotation_map = {
        list[str]: ARRAY(String)
    }


class UserWordORM(Base):
    __tablename__ = "user_word"

    user_id: Mapped[int] = mapped_column("user_id", ForeignKey("users.id"), primary_key=True)
    word_id: Mapped[int] = mapped_column("word_id", ForeignKey("words.id"), primary_key=True)
    rating: Mapped[float] = mapped_column("rating", Float(), default=0.0)
    attempts: Mapped[int] = mapped_column("attempts", Integer(), default=0)
    last_attempt: Mapped[datetime] = mapped_column("last_attempt", DateTime(), server_default=text("NOW() - INTERVAL '1 day'"))
    created_at: Mapped[datetime] = mapped_column("created_at", DateTime(), server_default="NOW()")

    user: Mapped["UserORM"] = relationship("UserORM", viewonly=True)
    word: Mapped["WordORM"] = relationship("WordORM", viewonly=True)


class WordORM(Base):
    __tablename__ = "words"

    id: Mapped[int] = mapped_column(Integer(), Identity(always=True), primary_key=True)
    en: Mapped[str] = mapped_column(unique=True)
    ru: Mapped[list[str]] = mapped_column(nullable=False)
    transcription: Mapped[str] = mapped_column(nullable=False)
    examples: Mapped[list[str] | None] = mapped_column(nullable=True)


class UserORM(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer(), Identity(always=True), primary_key=True)
    username: Mapped[str] = mapped_column(unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(Text(), nullable=False)
    role: Mapped[str] = mapped_column("role", String(), default="user")

    words: Mapped[list["WordORM"]] = relationship(
        secondary="user_word",
    )
