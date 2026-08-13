from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
from uuid import UUID


class ProductCreateRequest(BaseModel):
    """Schema for creating a new product."""
    
    category_id: UUID = Field(..., description="Category UUID")
    brand_id: Optional[UUID] = Field(None, description="Brand UUID (optional)")
    title: str = Field(..., min_length=1, max_length=255, description="Product display title")
    name: str = Field(..., min_length=1, max_length=255, description="URL slug (unique)")
    sku: str = Field(..., min_length=1, max_length=100, description="Stock Keeping Unit (unique)")
    mpn: Optional[str] = Field(None, max_length=100, description="Manufacturer Part Number")
    short_description: Optional[str] = Field(None, max_length=500, description="Brief overview")
    long_description: Optional[str] = Field(None, description="Full technical specifications")
    
    price: Decimal = Field(default=0, ge=0, description="Base selling price")
    compare_at_price: Optional[Decimal] = Field(None, ge=0, description="Original price for discounts")
    cost_price: Decimal = Field(default=0, ge=0, description="Internal cost of goods")
    
    stock_quantity: int = Field(default=0, ge=0, description="Current stock level")
    low_stock_threshold: int = Field(default=5, ge=0, description="Restock alert threshold")
    allow_backorders: bool = Field(default=False, description="Allow purchasing when out of stock")
    
    weight_kg: Optional[Decimal] = Field(None, ge=0, description="Weight in kg")
    length_cm: Optional[Decimal] = Field(None, ge=0, description="Length in cm")
    width_cm: Optional[Decimal] = Field(None, ge=0, description="Width in cm")
    height_cm: Optional[Decimal] = Field(None, ge=0, description="Height in cm")
    
    thumbnail_url: Optional[str] = Field(None, max_length=500, description="Main product image")
    is_featured: bool = Field(default=False, description="Featured status")
    
    is_discount: Optional[bool] = Field(None, description="On sale/discount flag")
    warranty: Optional[int] = Field(None, ge=0, description="Warranty in months")
    display_order: Optional[int] = Field(None, ge=0, description="Sort order")
    meta_title: Optional[str] = Field(None, max_length=255, description="SEO meta title")
    meta_description: Optional[str] = Field(None, max_length=500, description="SEO meta description")
    country_of_origin: Optional[str] = Field(None, max_length=100, description="Country of origin")
    
    is_active: bool = Field(default=True, description="Active status")


class ProductUpdateRequest(BaseModel):
    """Schema for updating a product."""
    
    category_id: Optional[UUID] = Field(None, description="Category UUID")
    brand_id: Optional[UUID] = Field(None, description="Brand UUID")
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="Product display title")
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="URL slug (unique)")
    sku: Optional[str] = Field(None, min_length=1, max_length=100, description="Stock Keeping Unit")
    mpn: Optional[str] = Field(None, max_length=100, description="Manufacturer Part Number")
    short_description: Optional[str] = Field(None, max_length=500, description="Brief overview")
    long_description: Optional[str] = Field(None, description="Full technical specifications")
    
    price: Optional[Decimal] = Field(None, ge=0, description="Base selling price")
    compare_at_price: Optional[Decimal] = Field(None, ge=0, description="Original price")
    cost_price: Optional[Decimal] = Field(None, ge=0, description="Internal cost")
    
    stock_quantity: Optional[int] = Field(None, ge=0, description="Current stock level")
    low_stock_threshold: Optional[int] = Field(None, ge=0, description="Restock threshold")
    allow_backorders: Optional[bool] = Field(None, description="Allow backorders")
    
    weight_kg: Optional[Decimal] = Field(None, ge=0, description="Weight in kg")
    length_cm: Optional[Decimal] = Field(None, ge=0, description="Length in cm")
    width_cm: Optional[Decimal] = Field(None, ge=0, description="Width in cm")
    height_cm: Optional[Decimal] = Field(None, ge=0, description="Height in cm")
    
    thumbnail_url: Optional[str] = Field(None, max_length=500, description="Main product image")
    is_featured: Optional[bool] = Field(None, description="Featured status")
    
    is_discount: Optional[bool] = Field(None, description="On sale/discount flag")
    warranty: Optional[int] = Field(None, ge=0, description="Warranty in months")
    display_order: Optional[int] = Field(None, ge=0, description="Sort order")
    meta_title: Optional[str] = Field(None, max_length=255, description="SEO meta title")
    meta_description: Optional[str] = Field(None, max_length=500, description="SEO meta description")
    country_of_origin: Optional[str] = Field(None, max_length=100, description="Country of origin")
    
    is_active: Optional[bool] = Field(None, description="Active status")
