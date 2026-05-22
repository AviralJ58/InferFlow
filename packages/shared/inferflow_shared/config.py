"""
Centralized configuration for InferFlow services.

Uses pydantic-settings to load configuration from environment variables
with sensible defaults for local development. Each service can extend
this base config with service-specific settings.
"""

from pydantic_settings import BaseSettings


class BaseConfig(BaseSettings):
    """Base configuration shared across all InferFlow services."""

    # Application
    app_env: str = "development"
    log_level: str = "INFO"

    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "inferflow"
    postgres_password: str = "inferflow_dev_password"
    postgres_db: str = "inferflow"

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379

    @property
    def database_url(self) -> str:
        """Construct async PostgreSQL DSN."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        """Construct Redis connection URL."""
        return f"redis://{self.redis_host}:{self.redis_port}/0"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}
