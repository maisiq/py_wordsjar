"""Application settings.

Everything is read from environment variables with the ``WORDSJAR_BACKEND_*``
prefix and, as a convenience for local development, from an optional ``.env``
file that lives next to the ``app`` package.

Paths are resolved from the location of this file, never from the current
working directory: the same code has to work when uvicorn is started from
``backend/app`` (local development) and from ``/app`` inside the container,
where the working directory is different and the ``.env`` file does not exist.
"""

import hashlib
import pathlib
import typing

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

APP_DIR = pathlib.Path(__file__).resolve().parent.parent
ENV_FILE = APP_DIR / ".env"

#: HS256 needs a key with enough entropy; anything shorter is a configuration bug.
MIN_SECRET_LENGTH = 32


class AppSettings(BaseSettings):
    debug: bool = False
    environment: typing.Literal["local", "staging", "production"] = "local"
    #: ``None`` keeps the interactive docs in sync with ``debug``.
    docs_enabled: bool | None = None

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf8",
        extra="ignore",
        env_prefix="WORDSJAR_BACKEND_APP_",
    )

    @property
    def docs(self) -> bool:
        if self.docs_enabled is not None:
            return self.docs_enabled
        return self.debug


class DatabaseSettings(BaseSettings):
    dsn: str
    echo: bool = False

    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: float = 10.0
    pool_recycle: int = 1800
    pool_pre_ping: bool = True

    connect_timeout: int = 5
    statement_timeout_ms: int = 15_000
    lock_timeout_ms: int = 5_000

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf8",
        extra="ignore",
        env_prefix="WORDSJAR_BACKEND_DB_",
    )

    @property
    def connect_args(self) -> dict[str, typing.Any]:
        # statement_timeout keeps a stuck query from pinning a pool connection
        # forever; connect_timeout keeps a dead database from hanging startup.
        options = " ".join(
            (
                f"-c statement_timeout={self.statement_timeout_ms}",
                f"-c lock_timeout={self.lock_timeout_ms}",
            )
        )
        return {
            "connect_timeout": self.connect_timeout,
            "options": options,
        }


class JWTSettings(BaseSettings):
    iss: str = "wordsjar"
    algorithm: str = "HS256"
    access_token_ttl: int = 12 * 60 * 60  # 12 hours
    refresh_token_ttl: int = 7 * 24 * 60 * 60  # 7 days

    #: Preferred source of the signing key. When it is empty the key is read
    #: from ``key_file_path`` (file-based development setup).
    key: SecretStr | None = None
    key_file_path: pathlib.Path = APP_DIR / "key"

    #: Optional dedicated secret for signing pagination cursors. When it is
    #: empty a value is derived from the signing key.
    cursor_secret: SecretStr | None = None

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf8",
        extra="ignore",
        env_prefix="WORDSJAR_BACKEND_JWT_",
    )

    @property
    def key_path(self) -> pathlib.Path:
        path = pathlib.Path(self.key_file_path)
        return path if path.is_absolute() else APP_DIR / path

    def read_signing_key(self) -> str:
        """Return the JWT signing key, failing early when it is unusable."""
        if self.key is not None:
            material = self.key.get_secret_value().strip()
            source = "WORDSJAR_BACKEND_JWT_KEY"
        else:
            source = str(self.key_path)
            try:
                material = self.key_path.read_text(encoding="utf8").strip()
            except OSError as exc:
                raise RuntimeError(
                    "JWT signing key is not configured: set WORDSJAR_BACKEND_JWT_KEY "
                    f"or provide a readable file at {self.key_path}"
                ) from exc

        if len(material) < MIN_SECRET_LENGTH:
            raise RuntimeError(
                f"JWT signing key from {source} is too short: "
                f"{len(material)} characters, {MIN_SECRET_LENGTH} required"
            )
        return material

    def read_cursor_secret(self) -> str:
        if self.cursor_secret is not None:
            material = self.cursor_secret.get_secret_value().strip()
            if len(material) < MIN_SECRET_LENGTH:
                raise RuntimeError(
                    "WORDSJAR_BACKEND_JWT_CURSOR_SECRET is too short: "
                    f"{len(material)} characters, {MIN_SECRET_LENGTH} required"
                )
            return material
        return hashlib.sha256(b"wordsjar/cursor/" + self.read_signing_key().encode()).hexdigest()


class CORSSettings(BaseSettings):
    origins: list[str] = Field(default_factory=list)
    allow_methods: list[str] = Field(default_factory=lambda: ["GET", "POST", "DELETE", "OPTIONS"])
    allow_headers: list[str] = Field(
        default_factory=lambda: [
            "Content-Type",
            "X-Auth-Token",
            "X-Refresh-Token",
            "X-Request-ID",
        ]
    )
    allow_credentials: bool = False

    #: Origins that were dropped because they cannot match a browser Origin.
    dropped_origins: list[str] = Field(default_factory=list, exclude=True)

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf8",
        extra="ignore",
        env_prefix="WORDSJAR_BACKEND_CORS_",
    )

    @model_validator(mode="after")
    def _normalize_origins(self) -> typing.Self:
        """Keep only real origins: a browser always sends scheme and host.

        ``localhost`` or ``127.0.0.1:3000`` can never match an ``Origin`` header,
        so a silent no-op is worse than dropping the entry loudly.
        """
        valid: list[str] = []
        dropped: list[str] = []
        for origin in self.origins:
            candidate = origin.strip()
            if candidate == "*" or candidate.startswith(("http://", "https://")):
                valid.append(candidate.rstrip("/"))
            else:
                dropped.append(origin)
        self.origins = valid
        self.dropped_origins = dropped
        return self


class Settings:
    """Container that owns every settings object exactly once."""

    def __init__(self) -> None:
        self.app = AppSettings()
        self.db = DatabaseSettings()
        self.jwt = JWTSettings()
        self.cors = CORSSettings()


_settings: Settings | None = None


def init() -> Settings:
    global _settings

    _settings = Settings()
    return _settings


def get_settings() -> Settings:
    if _settings is None:
        raise RuntimeError("config is not initialized")
    return _settings


def get_app_settings() -> AppSettings:
    return get_settings().app


def get_db_settings() -> DatabaseSettings:
    return get_settings().db


def get_jwt_settings() -> JWTSettings:
    return get_settings().jwt


def get_cors_settings() -> CORSSettings:
    return get_settings().cors