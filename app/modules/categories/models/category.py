import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Integer, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from app.utils.models.mixin.soft_delete import SoftDeleteMixin


class Category(Base, SoftDeleteMixin):
    """Category model for product/service categorization with display controls."""

    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    title: Mapped[str] = mapped_column(String(150), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False, unique=True, index=True)
    icon: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
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
        return f"<Category(id={self.id}, name={self.name}, title={self.title}, is_active={self.is_active})>"
