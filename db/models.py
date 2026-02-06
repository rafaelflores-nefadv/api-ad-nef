from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actor: Mapped[str] = mapped_column(String(255), nullable=False)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    object_type: Mapped[str] = mapped_column(String(64), nullable=False)
    object_id: Mapped[str] = mapped_column(String(255), nullable=False)
    result: Mapped[str] = mapped_column(String(32), nullable=False)
    details_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class UserMeta(Base):
    __tablename__ = "user_meta"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    ad_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    extra_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_sync: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class GroupMeta(Base):
    __tablename__ = "group_meta"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    groupname: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    ad_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    extra_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_sync: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
