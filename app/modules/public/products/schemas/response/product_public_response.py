from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from uuid import UUID
from decimal import Decimal


class ProductPublicBasicResponse(BaseModel):
    """Public schema for product list response (minimal fields)."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    title: str
    name: str
    price: Decimal
    thumbnail_url: Optional[str] = None
    brand_id: Optional[str] = None
    category_id: str


class ProductPublicFullResponse(BaseModel):
    """Public schema for product detail response (full fields, no audit data)."""
    
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
    
    stock_quantity: int
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
    country_of_origin: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None


class ProductPublicBasicCollection(BaseModel):
    """Collection of public products (basic)."""
    
    data: List[ProductPublicBasicResponse]
