from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base


class Announcement(Base):
    __tablename__ = "announcements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(100), default="General", nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    font_size: Mapped[str] = mapped_column(String(32), default="display-3", nullable=False)
    text_color: Mapped[str] = mapped_column(String(32), default="#FFFFFF", nullable=False)
    background_color: Mapped[str] = mapped_column(String(32), default="#111827", nullable=False)
    alignment: Mapped[str] = mapped_column(String(20), default="center", nullable=False)
    bold: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    italic: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    underline: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    animation: Mapped[str] = mapped_column(String(50), default="fade", nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
