from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "Campus Cat Association Map API"
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"

    database_host: str | None = None
    database_port: int = 5432
    database_name: str | None = None
    database_user: str | None = None
    database_password: str | None = None
    database_url: str | None = None

    @property
    def required_database_url(self) -> str:
        if not self.database_url:
            raise RuntimeError("CATMAP_DATABASE_URL is required for database operations")
        return self.database_url

    model_config = SettingsConfigDict(
        env_prefix="CATMAP_",
        env_file=BACKEND_DIR / ".env",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
