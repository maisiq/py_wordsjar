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


class CORSSettings(BaseSettings):
    origins: list[str]
    allow_methods: list[str]
    allow_headers: list[str]
    allow_credentials: bool

    model_config = SettingsConfigDict(
        yaml_file="config.yaml",
        yaml_config_section="cors",
        yaml_file_encoding="utf8",
        extra="ignore",
        case_sensitive=False,
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (YamlConfigSettingsSource(settings_cls),)

