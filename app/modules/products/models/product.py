from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Numeric
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from app.database import Base
from app.utils.soft_delete import SoftDeleteMixin


class Product(Base, SoftDeleteMixin):
    """Product model with inventory, pricing, and merchandising controls."""
    
    __tablename__ = "products"
    __table_args__ = {"schema": "dbo"}
    
    id = Column(UNIQUEIDENTIFIER, primary_key=True, default=lambda: UUID(int=0))
    
    # Relationships (UUID references without FK constraints)
    category_id = Column(String(36), nullable=False)  # Links to categories
    brand_id = Column(String(36), nullable=True)       # Links to brands (optional)
    
    # Core Information
    title = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False, unique=True, index=True)  # URL slug
    sku = Column(String(100), nullable=False, unique=True, index=True)   # Stock Keeping Unit
    mpn = Column(String(100), nullable=True)  # Manufacturer Part Number
    short_description = Column(String(500), nullable=True)
    long_description = Column(String, nullable=True)  # NVARCHAR(MAX)
    
    # Pricing & Financials
    price = Column(Numeric(18, 4), nullable=False, default=0.0)
    compare_at_price = Column(Numeric(18, 4), nullable=True)  # Original price for discounts
    cost_price = Column(Numeric(18, 4), nullable=False, default=0.0)  # Internal cost
    
    # Inventory Control
    stock_quantity = Column(Integer, nullable=False, default=0)
    low_stock_threshold = Column(Integer, nullable=False, default=5)
    allow_backorders = Column(Boolean, nullable=False, default=False)
    
    # Physical Properties
    weight_kg = Column(Numeric(10, 2), nullable=True)
    length_cm = Column(Numeric(10, 2), nullable=True)
    width_cm = Column(Numeric(10, 2), nullable=True)
    height_cm = Column(Numeric(10, 2), nullable=True)
    
    # Media & Merchandising
    thumbnail_url = Column(String(500), nullable=True)
    is_featured = Column(Boolean, nullable=False, default=False, index=True)
    visit_count = Column(Integer, nullable=False, default=0)
    
    # Additional Nullable Fields
    is_discount = Column(Boolean, nullable=True)  # On sale/discount flag
    warranty = Column(Integer, nullable=True)  # Warranty months
    display_order = Column(Integer, nullable=True, index=True)  # Sort order
    meta_title = Column(String(255), nullable=True)  # SEO meta title
    meta_description = Column(String(500), nullable=True)  # SEO meta description
    country_of_origin = Column(String(100), nullable=True)  # Country
    
    # Status
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    deleted_at = Column(DateTime, nullable=True, index=True)
    
    # Audit tracking (UUIDs without FK constraints)
    created_by = Column(String(36), nullable=False)  # UUID as string
    updated_by = Column(String(36), nullable=False)  # UUID as string
    deleted_by = Column(String(36), nullable=True)   # UUID as string
    
    def __repr__(self):
        return f"<Product(id={self.id}, name={self.name}, title={self.title}, is_active={self.is_active})>"
