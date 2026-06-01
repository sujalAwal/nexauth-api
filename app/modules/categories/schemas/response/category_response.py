from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class CategoryResponse(BaseModel):
    """Schema for category response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    title: str
    name: str
    icon: Optional[str] = None
    description: Optional[str] = None
    display_order: int
    is_featured: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    created_by: str
    updated_by: str
    deleted_by: Optional[str] = None


class CategoryCollection(BaseModel):
    """Collection response for multiple categories."""
    
    data: List[CategoryResponse]
