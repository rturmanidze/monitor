from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.settings import AppSetting

settings = get_settings()

DEFAULT_SETTINGS = {
    "company_name": settings.app_name,
    "company_logo": "",
    "theme": "dark",
    "accent_color": "#0d6efd",
    "default_font": "Inter",
    "default_text_color": "#FFFFFF",
    "default_background_color": "#111827",
    "pdf_rotation_interval": str(settings.pdf_rotation_interval),
    "announcement_animation": settings.announcement_transition,
    "transition_speed": str(settings.announcement_speed),
    "timezone": settings.app_timezone,
    "auto_backup_interval": str(settings.auto_backup_interval_minutes),
}


def ensure_settings(db: Session) -> None:
    existing = {row.key for row in db.query(AppSetting).all()}
    for key, value in DEFAULT_SETTINGS.items():
        if key not in existing:
            db.add(AppSetting(key=key, value=value, value_type="string"))
    db.commit()


def get_settings_map(db: Session) -> dict[str, str]:
    ensure_settings(db)
    return {row.key: row.value for row in db.query(AppSetting).all()}
