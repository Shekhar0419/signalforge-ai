from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SignalForge AI"
    app_env: str = "development"
    log_level: str = "INFO"

    max_upload_mb: int = 10
    upload_directory: str = "data/uploads"

    missing_warning_threshold: float = 0.20
    outlier_warning_threshold: float = 0.10

    database_url: str = "sqlite:///./signalforge.db"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()