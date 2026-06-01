from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from decimal import Decimal


class ProductResponse(BaseModel):
    """Schema for product response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    category_id: str
    brand_id: Optional[str] = None
    title: str
    name: str
    sku: str
    mpn: Optional[str] = None
    short_description: Optional[str] = None
    long_description: Optional[str] = None
    
    price: Decimal
    compare_at_price: Optional[Decimal] = None
    cost_price: Decimal
    
    stock_quantity: int
    low_stock_threshold: int
    allow_backorders: bool
    
    weight_kg: Optional[Decimal] = None
    length_cm: Optional[Decimal] = None
    width_cm: Optional[Decimal] = None
    height_cm: Optional[Decimal] = None
    
    thumbnail_url: Optional[str] = None
    is_featured: bool
    visit_count: int
    
    is_discount: Optional[bool] = None
    warranty: Optional[int] = None
    display_order: Optional[int] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    country_of_origin: Optional[str] = None
    
    is_active: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    created_by: str
    updated_by: str
    deleted_by: Optional[str] = None


class ProductCollection(BaseModel):
    """Collection response for multiple products."""
    
    data: List[ProductResponse]
