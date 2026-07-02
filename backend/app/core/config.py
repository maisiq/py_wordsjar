import pathlib

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = pathlib.Path(__name__).parent.parent


class AppSettings(BaseSettings):
    debug: bool

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        extra="ignore",
        env_prefix="WORDSJAR_BACKEND_APP_",
    )


class DatabaseSettings(BaseSettings):
    dsn: str

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        extra="ignore",
        env_prefix="WORDSJAR_BACKEND_DB_",
    )


class JWTSettings(BaseSettings):
    iss: str
    algorithm: str
    access_token_ttl: int = 60*60*12  # 12 hours
    refresh_token_ttl: int = 60*60*24*7  # 7 days
    key_file_path: pathlib.Path | str = BASE_DIR / "key"

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        extra="ignore",
        env_prefix="WORDSJAR_BACKEND_JWT_",
    )


class CORSSettings(BaseSettings):
    origins: list[str]
    allow_methods: list[str]
    allow_headers: list[str]
    allow_credentials: bool

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        extra="ignore",
        env_prefix="WORDSJAR_BACKEND_CORS_",
    )


_app_settings: AppSettings | None = None
_db_settings: DatabaseSettings | None = None
_jwt_settings: JWTSettings | None = None
_cors_settings: CORSSettings | None = None


def init():
    global _app_settings, _db_settings
    global _jwt_settings, _cors_settings

    _app_settings = AppSettings()
    _db_settings = DatabaseSettings()
    _jwt_settings = JWTSettings()
    _cors_settings = CORSSettings()


def get_app_settings() -> AppSettings:
    if _app_settings is None:
        raise RuntimeError("app_settings is not initialized")
    return _app_settings


def get_db_settings() -> DatabaseSettings:
    if _db_settings is None:
        raise RuntimeError("db_settings is not initialized")
    return _db_settings


def get_jwt_settings() -> JWTSettings:
    if _jwt_settings is None:
        raise RuntimeError("jwt_settings is not initialized")
    return _jwt_settings


def get_cors_settings() -> CORSSettings:
    if _cors_settings is None:
        raise RuntimeError("cors_settings is not initialized")
    return _cors_settings
