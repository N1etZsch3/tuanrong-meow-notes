from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "Campus Cat Association Map API"
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"
    cors_allow_origins: str = ""
    cors_allow_origin_regex: str = r"^https?://(localhost|127\.0\.0\.1|\[::1\])(:[0-9]+)?$"

    database_host: str | None = None
    database_port: int = 5432
    database_name: str | None = None
    database_user: str | None = None
    database_password: str | None = None
    database_url: str | None = None

    jwt_secret_key: str = "dev-only-change-me-with-at-least-32-bytes"
    jwt_algorithm: str = "HS256"
    access_token_expire_seconds: int = 604800
    captcha_secret_key: str = "dev-captcha-secret-change-me"
    captcha_expire_seconds: int = 300
    auth_lock_failed_attempts: int = 5
    auth_lock_minutes: int = 15
    amap_web_key: str = ""
    amap_web_service_key: str = ""
    amap_security_js_code: str = ""
    amap_web_service_timeout_seconds: float = 3.0
    tencent_map_key: str = ""
    tencent_map_secret_key: str = ""
    tencent_map_referer: str = "catmap-miniapp"
    tencent_map_service_timeout_seconds: float = 3.0
    tencent_cos_secret_id: str = ""
    tencent_cos_secret_key: str = ""
    tencent_cos_region: str = "ap-guangzhou"
    tencent_cos_bucket: str = ""
    tencent_cos_app_id: str = ""
    tencent_cos_scheme: str = "https"
    tencent_cos_domain: str = ""
    tencent_cos_cdn_domain: str = ""
    tencent_cos_env_prefix: str = "dev"
    file_upload_max_mb: int = 10
    file_image_max_pixels: int = 50_000_000

    @property
    def required_database_url(self) -> str:
        if not self.database_url:
            raise RuntimeError("CATMAP_DATABASE_URL is required for database operations")
        return self.database_url

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]

    @property
    def cors_origin_regex(self) -> str | None:
        regex = self.cors_allow_origin_regex.strip()
        return regex or None

    @property
    def file_upload_max_bytes(self) -> int:
        return self.file_upload_max_mb * 1024 * 1024

    @property
    def effective_amap_web_service_key(self) -> str:
        return self.amap_web_service_key or self.amap_web_key

    model_config = SettingsConfigDict(
        env_prefix="CATMAP_",
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8-sig",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
