from datetime import datetime, timezone
import uuid
from typing import Optional
from sqlalchemy import String, Integer, Boolean, DateTime, Enum, Index
from sqlalchemy.dialects.postgresql import UUID
from app.utils.enums.plan_tier import PlanTier
from app.utils.enums.industry import Industry
from app.database import Base
from app.utils.models.mixin.soft_delete import SoftDeleteMixin
from sqlalchemy.orm import Mapped, mapped_column


class Tenant(Base, SoftDeleteMixin):
    __tablename__ = "tenants"

    # ── Table-level indexes ──────────────────────────────────────────────────
    # GIN trigram indexes enable fast case-insensitive ILIKE search on text cols.
    # Requires: CREATE EXTENSION IF NOT EXISTS pg_trgm; (add to a migration)
    __table_args__ = (
        Index(
            "ix_tenants_name_trgm", "name",
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        ),
        Index(
            "ix_tenants_email_trgm", "contact_email",
            postgresql_using="gin",
            postgresql_ops={"contact_email": "gin_trgm_ops"},
        ),
    )

    # ── Columns ──────────────────────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    # Auto-generated from name by TenantService; must remain unique
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    # Auto-generated random 4-digit code (1000-9999) by TenantService
    code: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    plan_tier: Mapped[PlanTier] = mapped_column(
        Enum(PlanTier), nullable=False, index=True   # commonly filtered/sorted
    )
    industry: Mapped[Optional[Industry]] = mapped_column(Enum(Industry), nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # Optional custom domain / URL for the tenant
    domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, index=True              # hot path: filter by active status
    )
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),  # ORM sets this automatically on UPDATE
    )

    # ── Audit tracking fields ────────────────────────────────────────────────
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    deleted_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)