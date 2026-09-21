from functools import lru_cache
from typing import Literal
from urllib.parse import quote_plus

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: Literal["development", "test", "production"] = "development"
    log_level: str = "INFO"
    service_name: str = "nethealth-api"
    api_prefix: str = "/api"
    api_version_prefix: str = "/api/v1"
    backend_cors_origins: list[str] = Field(default_factory=lambda: ["http://127.0.0.1:3000"])

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "nethealth"
    database_user: str = "nethealth_app"
    database_password: SecretStr
    database_pool_size: int = Field(default=5, ge=1, le=50)

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = Field(default=0, ge=0)
    redis_password: SecretStr

    auth_cookie_name: str = "nethealth_session"
    auth_session_hours: int = Field(default=8, ge=1, le=168)
    auth_max_failed_attempts: int = Field(default=5, ge=1, le=20)
    auth_lockout_minutes: int = Field(default=15, ge=1, le=1440)

    collector_profiles_json: SecretStr = SecretStr("{}")
    collector_reachability_seconds: int = Field(default=30, ge=1, le=86400)
    collector_health_seconds: int = Field(default=60, ge=1, le=86400)
    collector_interfaces_seconds: int = Field(default=60, ge=1, le=86400)
    collector_optical_seconds: int = Field(default=180, ge=1, le=86400)
    collector_inventory_seconds: int = Field(default=1800, ge=1, le=86400)
    icmp_probe_attempts: int = Field(default=3, ge=1, le=20)
    syslog_enabled: bool = False
    syslog_bind_host: str = "127.0.0.1"
    syslog_port: int = Field(default=5514, ge=1024, le=65535)

    metrics_raw_retention_days: int = Field(default=30, ge=1)
    metrics_five_minute_retention_days: int = Field(default=180, ge=1)
    metrics_hourly_retention_days: int = Field(default=730, ge=1)
    correlation_window_seconds: int = Field(default=60, ge=30, le=120)

    @property
    def database_url(self) -> str:
        password = quote_plus(self.database_password.get_secret_value())
        user = quote_plus(self.database_user)
        return (
            f"postgresql+asyncpg://{user}:{password}@"
            f"{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        password = self.redis_password.get_secret_value()
        credentials = f":{quote_plus(password)}@"
        return f"redis://{credentials}{self.redis_host}:{self.redis_port}/{self.redis_db}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
