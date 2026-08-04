from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.backup import BackupRecord

settings = get_settings()


def create_backup(db: Session, source_db_path: Path) -> BackupRecord:
    settings.backups_dir.mkdir(parents=True, exist_ok=True)
    filename = f"backup-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.db"
    destination = settings.backups_dir / filename
    shutil.copy2(source_db_path, destination)
    record = BackupRecord(filename=filename, file_path=str(destination), file_size=destination.stat().st_size)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def restore_backup(db: Session, backup: BackupRecord, source_db_path: Path) -> None:
    shutil.copy2(backup.file_path, source_db_path)
    backup.restored_at = datetime.utcnow()
    db.add(backup)
    db.commit()
