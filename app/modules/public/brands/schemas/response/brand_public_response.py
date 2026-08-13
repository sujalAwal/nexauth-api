from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from uuid import UUID


class BrandPublicResponse(BaseModel):
    """Public schema for brand response (customer-facing)."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    title: str
    logo: Optional[str] = None
    description: Optional[str] = None


class BrandPublicCollection(BaseModel):
    """Collection of public brands."""
    
    data: List[BrandPublicResponse]
