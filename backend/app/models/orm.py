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
    last_attempt: Mapped[datetime] = mapped_column(
        "last_attempt",
        DateTime(timezone=True),
        server_default=text("now() - interval '1 day'"),
    )
    # A constant default froze every row at the moment the migration ran.
    created_at: Mapped[datetime] = mapped_column(
        "created_at", DateTime(timezone=True), server_default=text("now()")
    )

    user: Mapped["UserORM"] = relationship("UserORM", viewonly=True)
    word: Mapped["WordORM"] = relationship("WordORM", viewonly=True)


class AuthSessionORM(Base):
    """Refresh session, or a revoked access token, keyed by a hash of the token.

    Only the sha256 of a token is stored: a database dump does not expose usable
    refresh tokens.
    """

    __tablename__ = "auth_session"

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    #: ``refresh`` for a live session, ``access`` for a revoked access token.
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )

    user: Mapped["UserORM"] = relationship("UserORM", viewonly=True)


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
