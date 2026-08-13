import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey , UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from app.utils.models.mixin.soft_delete import SoftDeleteMixin

class TenantService(Base, SoftDeleteMixin):
    __tablename__ = "tenant_services"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'slug', name='uq_tenant_service_tenant_slug'),
    )
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False)
    
    # Basic Info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    api_tier: Mapped[str] = mapped_column(String(50), nullable=False)  # BASIC, PREMIUM, ENTERPRISE
    
    # Security
    secret_key: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    last_secret_key_generated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    secret_key_generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    secret_key_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    secret_key_generated_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    secret_key_regeneration_count: Mapped[int] = mapped_column(Integer, default=0)

    public_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    last_public_key_generated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    public_key_generated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    public_key_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    public_key_generated_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)

    webhook_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    webhook_secret: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Configuration
    rate_limit: Mapped[int] = mapped_column(Integer, default=1000)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    ip_whitelist: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Usage Tracking
    request_count: Mapped[int] = mapped_column(Integer, default=0)
    last_accessed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Timestamps & Audit
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    deleted_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)