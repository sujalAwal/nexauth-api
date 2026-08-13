from pydantic import BaseModel, Field
from typing import Optional


class BrandCreateRequest(BaseModel):
    """Schema for creating a new brand."""
    
    name: str = Field(..., min_length=1, max_length=150, description="Unique brand name")
    title: str = Field(..., min_length=1, max_length=150, description="Brand display title")
    logo: Optional[str] = Field(None, max_length=500, description="Logo URL")
    description: Optional[str] = Field(None, description="Brand description")
    website_url: Optional[str] = Field(None, max_length=255, description="Official website")
    country_of_origin: Optional[str] = Field(None, max_length=100, description="Country of origin")
    founded_year: Optional[int] = Field(None, ge=1800, le=2100, description="Year founded")
    is_featured: bool = Field(False, description="Featured status")
    is_active: bool = Field(True, description="Active status")


class BrandUpdateRequest(BaseModel):
    """Schema for updating a brand."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=150, description="Unique brand name")
    title: Optional[str] = Field(None, min_length=1, max_length=150, description="Brand display title")
    logo: Optional[str] = Field(None, max_length=500, description="Logo URL")
    description: Optional[str] = Field(None, description="Brand description")
    website_url: Optional[str] = Field(None, max_length=255, description="Official website")
    country_of_origin: Optional[str] = Field(None, max_length=100, description="Country of origin")
    founded_year: Optional[int] = Field(None, ge=1800, le=2100, description="Year founded")
    is_featured: Optional[bool] = Field(None, description="Featured status")
    is_active: Optional[bool] = Field(None, description="Active status")
