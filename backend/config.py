"""Backend configuration."""

from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "AI Portfolio API"
    VERSION: str = "3.0.0"

    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_DAYS: int = 7

    DATABASE_URL: str = "sqlite:///./portfolio.db"

    GROQ_API_KEY: str = ""
    NEWS_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    CORS_ORIGINS: str = "http://localhost:8501"

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, value: str) -> str:
        if len(value) < 32 or value.lower().startswith(("your-", "replace-")):
            raise ValueError(
                "SECRET_KEY must be a non-placeholder value of at least 32 characters"
            )
        return value

    @property
    def cors_origins(self) -> List[str]:
        return [
            origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()
        ]


@lru_cache()
def get_settings() -> Settings:
    return Settings()
