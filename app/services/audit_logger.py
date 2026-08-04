from __future__ import annotations

import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.log_entry import LogEntry

settings = get_settings()
logger = logging.getLogger("monitor-signage")


def configure_logging() -> None:
    if logger.handlers:
        return
    settings.logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = Path(settings.logs_dir) / "application.log"
    handler = RotatingFileHandler(log_path, maxBytes=2_000_000, backupCount=10)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    handler.setFormatter(formatter)
    logger.setLevel(settings.log_level.upper())
    logger.addHandler(handler)
    logger.addHandler(logging.StreamHandler())


def write_log(db: Session | None, level: str, message: str, context: dict[str, Any] | None = None) -> None:
    configure_logging()
    getattr(logger, level.lower(), logger.info)(message)
    if db is None:
        return
    db.add(LogEntry(level=level.upper(), message=message, context=json.dumps(context or {}, default=str)))
