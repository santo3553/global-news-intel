from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import os
from pathlib import Path


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    PROJECT_NAME: str = "Global News Intelligence"
    VERSION: str = "0.1.0"

    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_URL: str = "http://localhost:8000"
    CORS_ORIGINS: Union[str, List[str]] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    DATABASE_URL: str = "sqlite+aiosqlite:///./global_news.db"
    DATABASE_SYNC_URL: str = "sqlite:///./global_news.db"
    REDIS_URL: str = "redis://localhost:6379/0"

    LLM_PROVIDER: str = "mock"
    LLM_MODEL: str = "mistral-7b-instruct-v0.2.Q4_K_M.gguf"
    LLM_CONTEXT_SIZE: int = 4096
    LLM_TEMPERATURE: float = 0.1

    EMBEDDING_PROVIDER: str = "mock"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    GEOCODING_PROVIDER: str = "local_gazetteer"
    NOMINATIM_USER_AGENT: str = "global_news_intelligence_local"

    NEWS_FETCH_INTERVAL: int = 900
    MAX_ARTICLE_LENGTH: int = 12000
    MAX_ARTICLES_PER_FEED: int = 25

    CLUSTER_SIMILARITY_THRESHOLD: float = 0.75
    DEDUPLICATION_HASH_THRESHOLD: float = 0.92
    MAX_CLUSTER_TIME_WINDOW_HOURS: int = 72

    IMPORTANCE_HUMAN_WEIGHT: float = 0.25
    IMPORTANCE_GLOBAL_WEIGHT: float = 0.20
    IMPORTANCE_GEOGRAPHIC_WEIGHT: float = 0.15
    IMPORTANCE_ECONOMIC_WEIGHT: float = 0.10
    IMPORTANCE_POLITICAL_WEIGHT: float = 0.10
    IMPORTANCE_NOVELTY_WEIGHT: float = 0.10
    IMPORTANCE_VELOCITY_WEIGHT: float = 0.05
    IMPORTANCE_SOURCE_COVERAGE_WEIGHT: float = 0.05

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[3] / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
