from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from uuid import UUID


class CategoryPublicResponse(BaseModel):
    """Public schema for category response (customer-facing)."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    title: str
    icon: Optional[str] = None
    description: Optional[str] = None


class CategoryPublicCollection(BaseModel):
    """Collection of public categories."""
    
    data: List[CategoryPublicResponse]
