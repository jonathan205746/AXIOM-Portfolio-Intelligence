"""Backend configuration"""
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):

    APP_NAME: str = "AI Portfolio API"
    VERSION: str = "3.0.0"

    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_DAYS: int = 7

    DATABASE_URL: str = "sqlite:///./portfolio.db"

    GROQ_API_KEY: str = ""
    NEWS_API_KEY: str = ""
    GEMINI_API_KEY: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"

@lru_cache()
def get_settings():
    return Settings()