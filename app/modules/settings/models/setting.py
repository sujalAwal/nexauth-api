"""Setting Model - Individual settings with type and value"""
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from app.utils.models.mixin.audit import AuditMixin
from app.utils.models.mixin.soft_delete import SoftDeleteMixin


class Setting(Base, SoftDeleteMixin, AuditMixin):
    __tablename__ = "settings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    value: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    setting_group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("setting_groups.id"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
