from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "Campus Cat Association Map API"
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"
    cors_allow_origins: str = "*"

    database_host: str | None = None
    database_port: int = 5432
    database_name: str | None = None
    database_user: str | None = None
    database_password: str | None = None
    database_url: str | None = None

    jwt_secret_key: str = "dev-only-change-me-with-at-least-32-bytes"
    jwt_algorithm: str = "HS256"
    access_token_expire_seconds: int = 7200
    captcha_secret_key: str = "dev-captcha-secret-change-me"
    captcha_expire_seconds: int = 300
    auth_lock_failed_attempts: int = 5
    auth_lock_minutes: int = 15

    @property
    def required_database_url(self) -> str:
        if not self.database_url:
            raise RuntimeError("CATMAP_DATABASE_URL is required for database operations")
        return self.database_url

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]

    model_config = SettingsConfigDict(
        env_prefix="CATMAP_",
        env_file=BACKEND_DIR / ".env",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
