from pydantic import BaseModel, Field
from typing import Optional


class CategoryCreateRequest(BaseModel):
    """Schema for creating a new category."""
    
    title: str = Field(..., min_length=1, max_length=150, description="Category display title")
    name: str = Field(..., min_length=1, max_length=150, description="URL slug (unique)")
    icon: Optional[str] = Field(None, max_length=500, description="Icon/thumbnail URL")
    description: Optional[str] = Field(None, description="Category description")
    display_order: int = Field(0, ge=0, description="Sort order")
    is_featured: bool = Field(False, description="Featured status")
    is_active: bool = Field(True, description="Active status")


class CategoryUpdateRequest(BaseModel):
    """Schema for updating a category."""
    
    title: Optional[str] = Field(None, min_length=1, max_length=150, description="Category display title")
    name: Optional[str] = Field(None, min_length=1, max_length=150, description="URL slug (unique)")
    icon: Optional[str] = Field(None, max_length=500, description="Icon/thumbnail URL")
    description: Optional[str] = Field(None, description="Category description")
    display_order: Optional[int] = Field(None, ge=0, description="Sort order")
    is_featured: Optional[bool] = Field(None, description="Featured status")
    is_active: Optional[bool] = Field(None, description="Active status")
