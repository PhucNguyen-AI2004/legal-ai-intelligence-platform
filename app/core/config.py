from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AnyHttpUrl, Field, PostgresDsn, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.embedding_config import EMBEDDING_MODEL, VECTOR_DIMENSION

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
    secret_key: SecretStr
    access_token_expire_minutes: int = Field(default=30, ge=1, le=1440)
    algorithm: Literal["HS256"] = "HS256"
    document_storage_path: Path = Path("storage/documents")
    max_upload_size_mb: int = Field(default=20, ge=1, le=100)
    chunk_size: int = Field(default=1200, ge=100, le=20000)
    chunk_overlap: int = Field(default=200, ge=0)
    embedding_model_name: str = EMBEDDING_MODEL
    embedding_dimension: int = VECTOR_DIMENSION
    embedding_batch_size: int = Field(default=16, ge=1, le=128)
    hf_home: Path = Path(".cache/huggingface")
    llm_provider: str = "openai-compatible"
    llm_model: str = ""
    llm_api_key: SecretStr = SecretStr("")
    llm_base_url: str = ""
    llm_temperature: float = Field(default=0.1, ge=0, le=2, allow_inf_nan=False)
    llm_max_tokens: int = Field(default=800, ge=1, le=8192)
    llm_timeout_seconds: float = Field(default=60, ge=1, le=300, allow_inf_nan=False)
    rag_min_similarity: float = Field(default=0.45, ge=-1, le=1, allow_inf_nan=False)
    rag_max_context_chars: int = Field(default=12000, ge=100, le=50000)
    chat_history_max_messages: int = Field(default=6, ge=0, le=20)
    frontend_origin: AnyHttpUrl = AnyHttpUrl("http://localhost:3000")

    @field_validator("embedding_dimension")
    @classmethod
    def validate_embedding_dimension(cls, value: int) -> int:
        if value != VECTOR_DIMENSION:
            raise ValueError("EMBEDDING_DIMENSION must match the active vector schema")
        return value

    @field_validator("embedding_model_name")
    @classmethod
    def validate_embedding_model(cls, value: str) -> str:
        if value != EMBEDDING_MODEL:
            raise ValueError("This phase supports intfloat/multilingual-e5-small only")
        return value

    @property
    def model_cache_directory(self) -> Path:
        path = self.hf_home
        return (path if path.is_absolute() else PROJECT_ROOT / path).resolve()

    @model_validator(mode="after")
    def validate_chunk_overlap(self) -> "Settings":
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE")
        return self

    @property
    def storage_directory(self) -> Path:
        path = self.document_storage_path
        return (path if path.is_absolute() else PROJECT_ROOT / path).resolve()

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, value: SecretStr) -> SecretStr:
        secret = value.get_secret_value()
        if len(secret.encode("utf-8")) < 32 or len(set(secret)) < 8:
            raise ValueError("SECRET_KEY must be a random secret of at least 32 bytes")
        return value

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
