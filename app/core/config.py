from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="Monitor Signage", alias="APP_NAME")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=7010, alias="APP_PORT")
    app_timezone: str = Field(default="UTC", alias="APP_TIMEZONE")
    database_url: str = Field(default="sqlite:////app/database/monitor.db", alias="DATABASE_URL")
    secret_key: str = Field(default="change-me", alias="SECRET_KEY")
    default_admin_name: str = Field(default="System", alias="DEFAULT_ADMIN_NAME")
    pdf_rotation_interval: int = Field(default=12, alias="PDF_ROTATION_INTERVAL")
    announcement_transition: str = Field(default="fade", alias="ANNOUNCEMENT_TRANSITION")
    announcement_speed: int = Field(default=800, alias="ANNOUNCEMENT_SPEED")
    auto_backup_interval_minutes: int = Field(default=180, alias="AUTO_BACKUP_INTERVAL_MINUTES")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    uploads_dir: Path = BASE_DIR / "uploads"
    logs_dir: Path = BASE_DIR / "logs"
    backups_dir: Path = BASE_DIR / "backups"
    database_dir: Path = BASE_DIR / "database"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
