import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from app.utils.models.mixin.audit import AuditMixin
from app.utils.models.mixin.soft_delete import SoftDeleteMixin


class User(Base, SoftDeleteMixin, AuditMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    middle_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    country_code: Mapped[str] = mapped_column(String(5), nullable=False)
    state: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    municipality: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
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
    email_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
