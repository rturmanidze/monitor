from __future__ import annotations

import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import get_settings
from app.models.media import MediaType

settings = get_settings()


ALLOWED_CONTENT_TYPES = {
    "application/pdf": MediaType.PDF,
    "video/mp4": MediaType.MP4,
}


async def save_upload(upload: UploadFile) -> tuple[str, Path, int, MediaType]:
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(upload.filename or "").suffix.lower()
    content_type = upload.content_type or ""
    media_type = ALLOWED_CONTENT_TYPES.get(content_type)
    if media_type is None:
        if suffix == ".pdf":
            media_type = MediaType.PDF
        elif suffix == ".mp4":
            media_type = MediaType.MP4
        else:
            raise ValueError("Unsupported media type")
    unique_name = f"{uuid4().hex}{suffix or ('.pdf' if media_type == MediaType.PDF else '.mp4')}"
    destination = settings.uploads_dir / unique_name
    with destination.open("wb") as buffer:
        shutil.copyfileobj(upload.file, buffer)
    size = destination.stat().st_size
    return unique_name, destination, size, media_type


def remove_file(path: str) -> None:
    file_path = Path(path)
    if file_path.exists():
        file_path.unlink()
