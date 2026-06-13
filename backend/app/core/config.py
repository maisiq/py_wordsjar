import pathlib

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = pathlib.Path(__name__).parent.parent

ORIGINS = [
    "http://localhost",
    "http://localhost:8080",
    "http://frontend.local.test:3000",
]


JWT_ISS = "wordsjar"
JWT_ALGORITHM = "HS256"

ACCESS_TOKEN_TTL = 60*60*12  # 12 hours
REFRESH_TOKEN_TTL = 60*60*24*7  # 7 days

JWT_KEY_FILE_PATH = BASE_DIR / "key"


class AppSettings(BaseSettings):
    debug: bool

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        extra="ignore",
        env_prefix="APP_",
    )


class DatabaseSettings(BaseSettings):
    pg_dsn: str

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        extra="ignore",
    )
