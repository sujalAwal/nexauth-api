import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Text, DateTime, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID , JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy import Integer

from app.database import Base
from app.utils.models.mixin.audit import AuditMixin
from app.utils.models.mixin.soft_delete import SoftDeleteMixin


class Department(Base, SoftDeleteMixin):
    __tablename__ = "departments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
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

    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    deleted_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)

    sharepoint_links: Mapped[list["DepartmentSharepointLink"]] = relationship(
        "DepartmentSharepointLink",
        back_populates="department",
        cascade="all, delete-orphan",
        lazy="selectin"

    )


class DepartmentSharepointLink(Base, SoftDeleteMixin):
    __tablename__ = "department_sharepoint_links"
    __table_args__ = (
        UniqueConstraint("department_id", "sharepoint_url", name="uix_dept_sharepoint_url"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=False,
    )
    sharepoint_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    included_sites : Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    label: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sync_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_sync_status: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_sync_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

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

    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    deleted_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)

    department: Mapped[Department] = relationship("Department", back_populates="sharepoint_links")

class DepartmentPermission(Base, SoftDeleteMixin, AuditMixin):
    __tablename__ = "department_permissions"
    __table_args__ = (
        UniqueConstraint("user_id", "department", name="uq_department_permissions_user_department"),
    )

    id: Mapped[int] = mapped_column(
            Integer,
            primary_key=True,
            autoincrement=True,
        )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    department: Mapped[str] = mapped_column(String(100), nullable=False)
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

