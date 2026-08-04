import json
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.history import HistoryRecord


settings = get_settings()


def log_history(
    db: Session,
    *,
    object_type: str,
    object_id: str,
    action: str,
    old_value: Any = None,
    new_value: Any = None,
    administrator: str | None = None,
) -> None:
    entry = HistoryRecord(
        object_type=object_type,
        object_id=object_id,
        action=action,
        old_value=json.dumps(old_value, default=str) if old_value is not None else None,
        new_value=json.dumps(new_value, default=str) if new_value is not None else None,
        administrator=administrator or settings.default_admin_name,
    )
    db.add(entry)
