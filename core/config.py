from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or a local .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Alternative Financial Data API"
    app_description: str = "B2B API for extracting and serving structured financial data via GenAI."
    app_version: str = "0.1.0"

    api_key: str = "change-me"
    database_url: str = "sqlite:///./app.db"
    redis_url: str = "redis://localhost:6379/0"

    openai_api_key: str | None = None
    openai_base_url: str | None = None
    openai_model: str = "gpt-4o-mini"

    llm_backend: str = "openai"
    local_llm_endpoint: str | None = None

    http_proxy: str | None = None
    https_proxy: str | None = None
    scraper_proxy_url: str | None = None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()