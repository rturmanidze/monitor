from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.database.session import get_db
from app.models.announcement import Announcement
from app.models.backup import BackupRecord
from app.models.history import HistoryRecord
from app.models.media import Media, MediaType
from app.models.template import AnnouncementTemplate
from app.services.audit_logger import write_log
from app.services.backup_service import create_backup, restore_backup
from app.services.files import remove_file, save_upload
from app.services.history import log_history
from app.services.metrics import collect_dashboard_metrics
from app.services.settings_service import get_settings_map
from app.websocket.manager import manager

settings = get_settings()
router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parents[1] / "templates"))


@router.get("/", response_class=HTMLResponse)
def root() -> RedirectResponse:
    return RedirectResponse(url="/admin", status_code=302)


@router.get("/admin", response_class=HTMLResponse)
def admin(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    dashboard = collect_dashboard_metrics()
    media_items = db.query(Media).order_by(desc(Media.created_at)).all()
    announcements = db.query(Announcement).order_by(asc(Announcement.sort_order), desc(Announcement.priority)).all()
    templates_list = db.query(AnnouncementTemplate).order_by(AnnouncementTemplate.name).all()
    history = db.query(HistoryRecord).order_by(desc(HistoryRecord.created_at)).limit(20).all()
    backups = db.query(BackupRecord).order_by(desc(BackupRecord.created_at)).all()
    websocket_counts = manager.counts()
    return templates.TemplateResponse(
        request,
        "admin/index.html",
        {
            "dashboard": dashboard,
            "media_items": media_items,
            "announcements": announcements,
            "templates": templates_list,
            "history": history,
            "backups": backups,
            "websocket_counts": websocket_counts,
            "settings_map": get_settings_map(db),
            "now": datetime.utcnow(),
        },
    )


@router.get("/display/media", response_class=HTMLResponse)
def display_media(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    active_media = db.query(Media).filter(Media.is_active.is_(True)).one_or_none()
    return templates.TemplateResponse(request, "display/media.html", {"active_media": active_media, "settings_map": get_settings_map(db)})


@router.get("/display/live", response_class=HTMLResponse)
def display_live(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    announcements = db.query(Announcement).filter(Announcement.enabled.is_(True), Announcement.archived.is_(False)).order_by(Announcement.pinned.desc(), Announcement.sort_order.asc(), Announcement.priority.desc()).all()
    return templates.TemplateResponse(request, "display/live.html", {"announcements": announcements, "settings_map": get_settings_map(db)})


@router.get("/media/file/{media_id}")
def media_file(media_id: int, db: Session = Depends(get_db)) -> FileResponse:
    media = db.get(Media, media_id)
    if media is None:
        raise HTTPException(status_code=404, detail="Media not found")
    return FileResponse(media.file_path, filename=media.original_filename)


@router.post("/api/media")
async def upload_media(file: UploadFile = File(...), db: Session = Depends(get_db)) -> JSONResponse:
    stored_filename, destination, file_size, media_type = await save_upload(file)
    media = Media(
        original_filename=file.filename or stored_filename,
        stored_filename=stored_filename,
        file_path=str(destination),
        file_type=media_type,
        file_size=file_size,
        is_active=False,
    )
    db.add(media)
    log_history(db, object_type="media", object_id="new", action="uploaded", new_value={"filename": media.original_filename})
    write_log(db, "info", "Media uploaded", {"filename": media.original_filename, "type": media_type})
    db.commit()
    db.refresh(media)
    await manager.broadcast("media", "media-updated", {"media_id": media.id})
    return JSONResponse({"status": "ok", "media_id": media.id})


@router.post("/api/media/{media_id}/activate")
async def activate_media(media_id: int, db: Session = Depends(get_db)) -> JSONResponse:
    media = db.get(Media, media_id)
    if media is None:
        raise HTTPException(status_code=404, detail="Media not found")
    db.query(Media).filter(Media.is_active.is_(True)).update({Media.is_active: False})
    media.is_active = True
    db.add(media)
    log_history(db, object_type="media", object_id=str(media.id), action="activated", new_value={"filename": media.original_filename})
    write_log(db, "info", "Media activated", {"id": media.id})
    db.commit()
    await manager.broadcast("media", "media-updated", {"media_id": media.id, "active": True})
    return JSONResponse({"status": "ok"})


@router.post("/api/media/{media_id}/deactivate")
async def deactivate_media(media_id: int, db: Session = Depends(get_db)) -> JSONResponse:
    media = db.get(Media, media_id)
    if media is None:
        raise HTTPException(status_code=404, detail="Media not found")
    media.is_active = False
    db.add(media)
    log_history(db, object_type="media", object_id=str(media.id), action="deactivated", old_value={"filename": media.original_filename})
    write_log(db, "info", "Media deactivated", {"id": media.id})
    db.commit()
    await manager.broadcast("media", "media-updated", {"media_id": media.id, "active": False})
    return JSONResponse({"status": "ok"})


@router.delete("/api/media/{media_id}")
async def delete_media(media_id: int, db: Session = Depends(get_db)) -> JSONResponse:
    media = db.get(Media, media_id)
    if media is None:
        raise HTTPException(status_code=404, detail="Media not found")
    remove_file(media.file_path)
    log_history(db, object_type="media", object_id=str(media.id), action="deleted", old_value={"filename": media.original_filename})
    write_log(db, "warning", "Media deleted", {"id": media.id})
    db.delete(media)
    db.commit()
    await manager.broadcast("media", "media-updated", {"media_id": media_id, "deleted": True})
    return JSONResponse({"status": "ok"})


@router.post("/api/announcements")
def create_announcement(
    title: str = Form(...),
    message: str = Form(...),
    category: str = Form("General"),
    priority: int = Form(0),
    duration_seconds: int = Form(10),
    font_size: str = Form("display-3"),
    text_color: str = Form("#FFFFFF"),
    background_color: str = Form("#111827"),
    alignment: str = Form("center"),
    bold: bool = Form(False),
    italic: bool = Form(False),
    underline: bool = Form(False),
    animation: str = Form("fade"),
    enabled: bool = Form(True),
    pinned: bool = Form(False),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    next_order = (db.query(Announcement).order_by(desc(Announcement.sort_order)).first().sort_order + 1) if db.query(Announcement).count() else 1
    announcement = Announcement(
        title=title,
        message=message,
        category=category,
        priority=priority,
        duration_seconds=duration_seconds,
        font_size=font_size,
        text_color=text_color,
        background_color=background_color,
        alignment=alignment,
        bold=bold,
        italic=italic,
        underline=underline,
        animation=animation,
        enabled=enabled,
        pinned=pinned,
        sort_order=next_order,
    )
    db.add(announcement)
    log_history(db, object_type="announcement", object_id="new", action="created", new_value={"title": title})
    write_log(db, "info", "Announcement created", {"title": title})
    db.commit()
    db.refresh(announcement)
    import asyncio
    asyncio.run(manager.broadcast("live", "announcements-updated", {"announcement_id": announcement.id}))
    return RedirectResponse(url="/admin", status_code=303)


@router.post("/api/announcements/{announcement_id}/update")
def update_announcement(
    announcement_id: int,
    title: str = Form(...),
    message: str = Form(...),
    category: str = Form(...),
    priority: int = Form(...),
    duration_seconds: int = Form(...),
    font_size: str = Form(...),
    text_color: str = Form(...),
    background_color: str = Form(...),
    alignment: str = Form(...),
    bold: bool = Form(False),
    italic: bool = Form(False),
    underline: bool = Form(False),
    animation: str = Form(...),
    enabled: bool = Form(False),
    pinned: bool = Form(False),
    archived: bool = Form(False),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    announcement = db.get(Announcement, announcement_id)
    if announcement is None:
        raise HTTPException(status_code=404, detail="Announcement not found")
    old_payload = {"title": announcement.title, "message": announcement.message}
    for key, value in {
        "title": title,
        "message": message,
        "category": category,
        "priority": priority,
        "duration_seconds": duration_seconds,
        "font_size": font_size,
        "text_color": text_color,
        "background_color": background_color,
        "alignment": alignment,
        "bold": bold,
        "italic": italic,
        "underline": underline,
        "animation": animation,
        "enabled": enabled,
        "pinned": pinned,
        "archived": archived,
    }.items():
        setattr(announcement, key, value)
    db.add(announcement)
    log_history(db, object_type="announcement", object_id=str(announcement.id), action="updated", old_value=old_payload, new_value={"title": title, "message": message})
    write_log(db, "info", "Announcement updated", {"id": announcement.id})
    db.commit()
    import asyncio
    asyncio.run(manager.broadcast("live", "announcements-updated", {"announcement_id": announcement.id}))
    return RedirectResponse(url="/admin", status_code=303)


@router.post("/api/announcements/{announcement_id}/duplicate")
def duplicate_announcement(announcement_id: int, db: Session = Depends(get_db)) -> RedirectResponse:
    announcement = db.get(Announcement, announcement_id)
    if announcement is None:
        raise HTTPException(status_code=404, detail="Announcement not found")
    clone = Announcement(
        title=f"{announcement.title} Copy",
        message=announcement.message,
        category=announcement.category,
        priority=announcement.priority,
        sort_order=announcement.sort_order + 1,
        duration_seconds=announcement.duration_seconds,
        font_size=announcement.font_size,
        text_color=announcement.text_color,
        background_color=announcement.background_color,
        alignment=announcement.alignment,
        bold=announcement.bold,
        italic=announcement.italic,
        underline=announcement.underline,
        animation=announcement.animation,
        enabled=announcement.enabled,
        pinned=announcement.pinned,
        archived=False,
    )
    db.add(clone)
    log_history(db, object_type="announcement", object_id=str(announcement.id), action="duplicated", new_value={"title": clone.title})
    write_log(db, "info", "Announcement duplicated", {"source_id": announcement.id})
    db.commit()
    import asyncio
    asyncio.run(manager.broadcast("live", "announcements-updated", {"announcement_id": clone.id}))
    return RedirectResponse(url="/admin", status_code=303)


@router.post("/api/announcements/{announcement_id}/delete")
def delete_announcement(announcement_id: int, db: Session = Depends(get_db)) -> RedirectResponse:
    announcement = db.get(Announcement, announcement_id)
    if announcement is None:
        raise HTTPException(status_code=404, detail="Announcement not found")
    log_history(db, object_type="announcement", object_id=str(announcement.id), action="deleted", old_value={"title": announcement.title})
    write_log(db, "warning", "Announcement deleted", {"id": announcement.id})
    db.delete(announcement)
    db.commit()
    import asyncio
    asyncio.run(manager.broadcast("live", "announcements-updated", {"announcement_id": announcement_id, "deleted": True}))
    return RedirectResponse(url="/admin", status_code=303)


@router.post("/api/announcements/reorder")
def reorder_announcements(request: Request, db: Session = Depends(get_db)) -> JSONResponse:
    payload = json.loads(request.query_params.get("payload", "[]"))
    for index, item in enumerate(payload, start=1):
        announcement = db.get(Announcement, int(item["id"]))
        if announcement:
            announcement.sort_order = index
            db.add(announcement)
    db.commit()
    return JSONResponse({"status": "ok"})


@router.post("/api/templates")
def create_template(
    name: str = Form(...),
    category: str = Form(...),
    title: str = Form(...),
    message: str = Form(...),
    font_size: str = Form("display-3"),
    text_color: str = Form("#FFFFFF"),
    background_color: str = Form("#111827"),
    alignment: str = Form("center"),
    bold: bool = Form(False),
    italic: bool = Form(False),
    underline: bool = Form(False),
    animation: str = Form("fade"),
    duration_seconds: int = Form(10),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    record = AnnouncementTemplate(
        name=name,
        category=category,
        title=title,
        message=message,
        font_size=font_size,
        text_color=text_color,
        background_color=background_color,
        alignment=alignment,
        bold=bold,
        italic=italic,
        underline=underline,
        animation=animation,
        duration_seconds=duration_seconds,
    )
    db.add(record)
    log_history(db, object_type="template", object_id="new", action="created", new_value={"name": name})
    db.commit()
    return RedirectResponse(url="/admin", status_code=303)


@router.post("/api/templates/{template_id}/apply")
def apply_template(template_id: int, db: Session = Depends(get_db)) -> JSONResponse:
    template = db.get(AnnouncementTemplate, template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return JSONResponse({
        "title": template.title,
        "message": template.message,
        "category": template.category,
        "font_size": template.font_size,
        "text_color": template.text_color,
        "background_color": template.background_color,
        "alignment": template.alignment,
        "bold": template.bold,
        "italic": template.italic,
        "underline": template.underline,
        "animation": template.animation,
        "duration_seconds": template.duration_seconds,
    })




@router.get("/api/announcements/feed")
def announcements_feed(db: Session = Depends(get_db)) -> JSONResponse:
    announcements = db.query(Announcement).order_by(Announcement.pinned.desc(), Announcement.sort_order.asc(), Announcement.priority.desc()).all()
    data = [{"id": row.id, "title": row.title, "message": row.message, "category": row.category, "priority": row.priority, "sort_order": row.sort_order, "duration_seconds": row.duration_seconds, "font_size": row.font_size, "text_color": row.text_color, "background_color": row.background_color, "alignment": row.alignment, "bold": row.bold, "italic": row.italic, "underline": row.underline, "animation": row.animation, "enabled": row.enabled, "pinned": row.pinned, "archived": row.archived} for row in announcements]
    return JSONResponse(data)

@router.get("/api/history")
def history_feed(db: Session = Depends(get_db)) -> JSONResponse:
    history = db.query(HistoryRecord).order_by(desc(HistoryRecord.created_at)).limit(100).all()
    data = [{"id": row.id, "object_type": row.object_type, "action": row.action, "administrator": row.administrator, "created_at": row.created_at.isoformat(), "old_value": row.old_value, "new_value": row.new_value} for row in history]
    return JSONResponse(data)


@router.post("/api/backups/create")
def manual_backup(db: Session = Depends(get_db)) -> RedirectResponse:
    source = Path(settings.database_dir) / "monitor.db"
    if not source.exists():
        raise HTTPException(status_code=404, detail="Database file not found")
    create_backup(db, source)
    return RedirectResponse(url="/admin", status_code=303)


@router.post("/api/backups/{backup_id}/restore")
def restore_backup_route(backup_id: int, db: Session = Depends(get_db)) -> RedirectResponse:
    backup = db.get(BackupRecord, backup_id)
    if backup is None:
        raise HTTPException(status_code=404, detail="Backup not found")
    source = Path(settings.database_dir) / "monitor.db"
    restore_backup(db, backup, source)
    return RedirectResponse(url="/admin", status_code=303)
