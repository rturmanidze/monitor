from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base


class AnnouncementTemplate(Base):
    __tablename__ = "templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    font_size: Mapped[str] = mapped_column(String(32), default="display-3", nullable=False)
    text_color: Mapped[str] = mapped_column(String(32), default="#FFFFFF", nullable=False)
    background_color: Mapped[str] = mapped_column(String(32), default="#111827", nullable=False)
    alignment: Mapped[str] = mapped_column(String(20), default="center", nullable=False)
    bold: Mapped[bool] = mapped_column(default=True, nullable=False)
    italic: Mapped[bool] = mapped_column(default=False, nullable=False)
    underline: Mapped[bool] = mapped_column(default=False, nullable=False)
    animation: Mapped[str] = mapped_column(String(50), default="fade", nullable=False)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
