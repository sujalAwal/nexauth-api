import uuid
from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Integer, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.utils.models.mixin.soft_delete import SoftDeleteMixin

if TYPE_CHECKING:
    from .countries import Country
    from .districts import District


class Province(Base, SoftDeleteMixin):
    __tablename__ = "provinces"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(10), nullable=False)
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
    country_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("countries.id"), nullable=False)
    name_np: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    province_order: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    updated_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    deleted_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)

    country: Mapped["Country"] = relationship("Country", backref="provinces")
    districts: Mapped[List["District"]] = relationship("District", back_populates="province")

    __table_args__ = (
        Index("IX_provinces_code", "code"),
        Index("IX_provinces_country_id", "country_id"),
    )
