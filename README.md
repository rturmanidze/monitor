# Digital Signage Management System

Production-ready self-hosted digital signage platform for two company monitors.

## URLs
- Admin dashboard: http://localhost:7010/admin
- Media display: http://localhost:7010/display/media
- Live display: http://localhost:7010/display/live

## Features
- FastAPI + SQLAlchemy + SQLite + Alembic backend
- Bootstrap 5 dark admin dashboard
- PDF/MP4 media upload, preview, activation, replacement, deletion
- Live announcements with templates, ordering, styling, pinning, archiving, duplication
- Real-time updates over WebSockets for both display clients
- Permanent history, structured logs, manual and scheduled backups
- Dockerized deployment with persistent volumes

## Installation
```bash
docker compose up -d --build
```

## Docker Commands
```bash
docker compose up -d --build
docker compose logs -f
docker compose down
docker compose restart
```

## Project Structure
```text
app/
  api/
  core/
  database/
  models/
  services/
  websocket/
  templates/
  static/
alembic/
database/
uploads/
logs/
backups/
Dockerfile
docker-compose.yml
requirements.txt
README.md
.env.example
```

## Configuration
Copy `.env.example` to `.env` and adjust values if needed.

Key settings:
- `APP_NAME`
- `DATABASE_URL`
- `PDF_ROTATION_INTERVAL`
- `ANNOUNCEMENT_TRANSITION`
- `ANNOUNCEMENT_SPEED`
- `AUTO_BACKUP_INTERVAL_MINUTES`
- `LOG_LEVEL`

## Storage
Persistent host directories:
- `database/`
- `uploads/`
- `logs/`
- `backups/`

## Backup Instructions
- Manual backup: use the **Manual Backup** button in `/admin`
- Automatic backup: runs on configured interval
- Restore: use restore button in backup table

## Updating
```bash
git pull
docker compose up -d --build
```

## Troubleshooting
- If containers fail, inspect logs with `docker compose logs -f`
- If database schema is outdated, rebuild container so Alembic runs on startup
- Ensure port `7010` is free on the host
- Uploaded files and backups persist in mounted directories

## Screenshots
- `docs/screenshots/admin-dashboard.png`
- `docs/screenshots/media-display.png`
- `docs/screenshots/live-display.png`

## Notes
- No authentication is enabled by design
- Only one media asset can be active at a time
- History is never auto-deleted
