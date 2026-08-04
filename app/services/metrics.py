from __future__ import annotations

from datetime import datetime
from pathlib import Path

from app.core.config import get_settings
from app.database.session import SessionLocal
from app.models.announcement import Announcement
from app.models.backup import BackupRecord
from app.models.history import HistoryRecord
from app.models.media import Media

settings = get_settings()
START_TIME = datetime.utcnow()


def _dir_size(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def collect_dashboard_metrics() -> dict[str, object]:
    with SessionLocal() as db:
        active_media = db.query(Media).filter(Media.is_active.is_(True)).one_or_none()
        active_announcements = db.query(Announcement).filter(Announcement.enabled.is_(True), Announcement.archived.is_(False)).count()
        history_count = db.query(HistoryRecord).count()
        backup_count = db.query(BackupRecord).count()
        return {
            "active_media": active_media,
            "active_announcements": active_announcements,
            "history_count": history_count,
            "backup_count": backup_count,
            "storage_usage": {
                "database": _dir_size(settings.database_dir),
                "uploads": _dir_size(settings.uploads_dir),
                "logs": _dir_size(settings.logs_dir),
                "backups": _dir_size(settings.backups_dir),
            },
            "uptime_seconds": int((datetime.utcnow() - START_TIME).total_seconds()),
            "database_status": "online",
        }
