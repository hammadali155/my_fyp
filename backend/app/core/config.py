from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Jawhar API"
    app_version: str = "0.1.0"
    debug: bool = False

    database_url: str = "sqlite+aiosqlite:///./jawhar.db"

    jwt_secret: str = "CHANGE-ME-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    cors_origins: list[str] = ["*"]

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.0-flash"
    gemini_timeout_seconds: float = 20.0
    gemini_max_retries: int = 2
    gemini_retry_backoff_seconds: float = 0.5

    tutor_context_max_chars: int = 6000
    tutor_daily_message_limit: int = 40
    tutor_history_max_tokens: int = 2000

    farasa_url: str = "http://localhost:8765"
    farasa_timeout_seconds: float = 10.0

    log_level: str = "INFO"
    log_json: bool = False

    @property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parent.parent.parent

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    @property
    def database_url_asyncpg(self) -> str:
        """Return DATABASE_URL with the asyncpg driver for PostgreSQL URLs.

        SQLAlchemy defaults to psycopg for bare 'postgresql://' URLs, but we
        use asyncpg. Normalize 'postgresql://' -> 'postgresql+asyncpg://'
        so the driver is correct regardless of what the operator sets.
        """
        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return self.database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
