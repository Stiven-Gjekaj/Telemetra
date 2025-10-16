"""
Configuration module for Telemetra backend.
Loads settings from environment variables with sensible defaults.
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "Telemetra API"
    app_version: str = "0.1.0"
    debug: bool = Field(default=False, validation_alias="DEBUG")

    # Server
    host: str = Field(default="0.0.0.0", validation_alias="HOST")
    port: int = Field(default=8000, validation_alias="PORT")

    # Database
    postgres_host: str = Field(default="localhost", validation_alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, validation_alias="POSTGRES_PORT")
    postgres_db: str = Field(default="telemetra", validation_alias="POSTGRES_DB")
    postgres_user: str = Field(default="telemetra_user", validation_alias="POSTGRES_USER")
    postgres_password: str = Field(default="telemetra_pass", validation_alias="POSTGRES_PASSWORD")

    # Database connection pool settings
    db_pool_min_size: int = Field(default=5, validation_alias="DB_POOL_MIN_SIZE")
    db_pool_max_size: int = Field(default=20, validation_alias="DB_POOL_MAX_SIZE")
    db_pool_timeout: int = Field(default=30, validation_alias="DB_POOL_TIMEOUT")

    # Redis
    redis_host: str = Field(default="localhost", validation_alias="REDIS_HOST")
    redis_port: int = Field(default=6379, validation_alias="REDIS_PORT")
    redis_db: int = Field(default=0, validation_alias="REDIS_DB")
    redis_password: Optional[str] = Field(default=None, validation_alias="REDIS_PASSWORD")

    # Redis cache TTL (seconds)
    cache_ttl_metrics: int = Field(default=60, validation_alias="CACHE_TTL_METRICS")
    cache_ttl_streams: int = Field(default=300, validation_alias="CACHE_TTL_STREAMS")

    # WebSocket
    ws_heartbeat_interval: int = Field(default=30, validation_alias="WS_HEARTBEAT_INTERVAL")
    ws_message_interval: float = Field(default=1.5, validation_alias="WS_MESSAGE_INTERVAL")

    # CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        validation_alias="CORS_ORIGINS"
    )

    # Logging
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")

    @property
    def database_url(self) -> str:
        """Construct database URL for asyncpg."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        """Construct Redis URL."""
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
