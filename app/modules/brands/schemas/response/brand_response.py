from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class BrandResponse(BaseModel):
    """Schema for brand response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    title: str
    logo: Optional[str] = None
    description: Optional[str] = None
    website_url: Optional[str] = None
    country_of_origin: Optional[str] = None
    founded_year: Optional[int] = None
    visit_count: int
    is_featured: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    created_by: str
    updated_by: str
    deleted_by: Optional[str] = None


class BrandCollection(BaseModel):
    """Collection response for multiple brands."""
    
    data: List[BrandResponse]
