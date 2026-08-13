import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Integer, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from app.utils.models.mixin.soft_delete import SoftDeleteMixin


class Brand(Base, SoftDeleteMixin):
    """Brand model with corporate identity and analytics tracking."""

    __tablename__ = "brands"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    name: Mapped[str] = mapped_column(String(150), nullable=False, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    logo: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    website_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    country_of_origin: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    founded_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    visit_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_featured: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    updated_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    deleted_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)

    def __repr__(self):
        return f"<Brand(id={self.id}, name={self.name}, is_active={self.is_active})>"
