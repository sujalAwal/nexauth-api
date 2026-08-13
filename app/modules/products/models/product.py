import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from sqlalchemy import String, Integer, DateTime, Boolean, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from app.utils.models.mixin.soft_delete import SoftDeleteMixin


class Product(Base, SoftDeleteMixin):
    """Product model with inventory, pricing, and merchandising controls."""

    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    category_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    brand_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    sku: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    mpn: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    short_description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    long_description: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0.0"))
    compare_at_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4), nullable=True)
    cost_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0.0"))

    stock_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    low_stock_threshold: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    allow_backorders: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    weight_kg: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    length_cm: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    width_cm: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    height_cm: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)

    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    visit_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    is_discount: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    warranty: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    display_order: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    meta_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    meta_description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    country_of_origin: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

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
        return f"<Product(id={self.id}, name={self.name}, title={self.title}, is_active={self.is_active})>"
