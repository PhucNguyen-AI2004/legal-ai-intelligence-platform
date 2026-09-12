from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",  # The shared .env also contains Compose variables.
        hide_input_in_errors=True,
    )

    app_name: str = Field(min_length=1)
    app_env: Literal["development", "test", "production"]
    database_url: PostgresDsn

    @field_validator("database_url")
    @classmethod
    def require_psycopg(cls, value: PostgresDsn) -> PostgresDsn:
        if value.scheme != "postgresql+psycopg":
            raise ValueError("DATABASE_URL must use postgresql+psycopg://")
        if not value.path or value.path == "/":
            raise ValueError("DATABASE_URL must include a database name")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
