from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.core.config import get_settings
from app.database.session import Base, engine, SessionLocal
from app.models import *  # noqa: F401,F403
from app.services.audit_logger import configure_logging, write_log
from app.services.settings_service import ensure_settings
from app.websocket.manager import manager

settings = get_settings()
heartbeat_task: asyncio.Task | None = None
backup_task: asyncio.Task | None = None


async def backup_scheduler() -> None:
    from app.services.backup_service import create_backup

    while True:
        await asyncio.sleep(settings.auto_backup_interval_minutes * 60)
        source = Path(settings.database_dir) / "monitor.db"
        if source.exists():
            with SessionLocal() as db:
                create_backup(db, source)
                write_log(db, "info", "Scheduled backup created")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global heartbeat_task, backup_task
    configure_logging()
    settings.database_dir.mkdir(parents=True, exist_ok=True)
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    settings.logs_dir.mkdir(parents=True, exist_ok=True)
    settings.backups_dir.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        ensure_settings(db)
        write_log(db, "info", "Application startup")
        db.commit()
    heartbeat_task = asyncio.create_task(manager.heartbeat())
    backup_task = asyncio.create_task(backup_scheduler())
    yield
    if heartbeat_task:
        heartbeat_task.cancel()
    if backup_task:
        backup_task.cancel()
    with SessionLocal() as db:
        write_log(db, "info", "Application shutdown")
        db.commit()


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(Path(__file__).resolve().parent / "static")), name="static")
app.include_router(router)


@app.websocket("/ws/{channel}")
async def websocket_endpoint(websocket: WebSocket, channel: str) -> None:
    await manager.connect(channel, websocket)
    with SessionLocal() as db:
        write_log(db, "info", "WebSocket connected", {"channel": channel})
        db.commit()
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text('{"event":"pong"}')
    except WebSocketDisconnect:
        await manager.disconnect(channel, websocket)
        with SessionLocal() as db:
            write_log(db, "info", "WebSocket disconnected", {"channel": channel})
            db.commit()
