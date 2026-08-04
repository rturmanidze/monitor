"""initial

Revision ID: 20260804_000001
Revises: 
Create Date: 2026-08-04 00:00:01
"""

from alembic import op
import sqlalchemy as sa


revision = "20260804_000001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "announcements",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=False),
        sa.Column("font_size", sa.String(length=32), nullable=False),
        sa.Column("text_color", sa.String(length=32), nullable=False),
        sa.Column("background_color", sa.String(length=32), nullable=False),
        sa.Column("alignment", sa.String(length=20), nullable=False),
        sa.Column("bold", sa.Boolean(), nullable=False),
        sa.Column("italic", sa.Boolean(), nullable=False),
        sa.Column("underline", sa.Boolean(), nullable=False),
        sa.Column("animation", sa.String(length=50), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("pinned", sa.Boolean(), nullable=False),
        sa.Column("archived", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index(op.f("ix_announcements_id"), "announcements", ["id"], unique=False)
    op.create_table(
        "backups",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("restored_at", sa.DateTime(), nullable=True),
    )
    op.create_index(op.f("ix_backups_id"), "backups", ["id"], unique=False)
    op.create_table(
        "history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("object_type", sa.String(length=100), nullable=False),
        sa.Column("object_id", sa.String(length=100), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("old_value", sa.Text(), nullable=True),
        sa.Column("new_value", sa.Text(), nullable=True),
        sa.Column("administrator", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(op.f("ix_history_id"), "history", ["id"], unique=False)
    op.create_table(
        "logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("level", sa.String(length=20), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("context", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(op.f("ix_logs_id"), "logs", ["id"], unique=False)
    op.create_table(
        "media",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("stored_filename", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("file_type", sa.Enum("PDF", "MP4", name="mediatype"), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index(op.f("ix_media_id"), "media", ["id"], unique=False)
    op.create_table(
        "settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("value_type", sa.String(length=50), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index(op.f("ix_settings_id"), "settings", ["id"], unique=False)
    op.create_table(
        "templates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("font_size", sa.String(length=32), nullable=False),
        sa.Column("text_color", sa.String(length=32), nullable=False),
        sa.Column("background_color", sa.String(length=32), nullable=False),
        sa.Column("alignment", sa.String(length=20), nullable=False),
        sa.Column("bold", sa.Boolean(), nullable=False),
        sa.Column("italic", sa.Boolean(), nullable=False),
        sa.Column("underline", sa.Boolean(), nullable=False),
        sa.Column("animation", sa.String(length=50), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index(op.f("ix_templates_id"), "templates", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_templates_id"), table_name="templates")
    op.drop_table("templates")
    op.drop_index(op.f("ix_settings_id"), table_name="settings")
    op.drop_table("settings")
    op.drop_index(op.f("ix_media_id"), table_name="media")
    op.drop_table("media")
    op.drop_index(op.f("ix_logs_id"), table_name="logs")
    op.drop_table("logs")
    op.drop_index(op.f("ix_history_id"), table_name="history")
    op.drop_table("history")
    op.drop_index(op.f("ix_backups_id"), table_name="backups")
    op.drop_table("backups")
    op.drop_index(op.f("ix_announcements_id"), table_name="announcements")
    op.drop_table("announcements")
