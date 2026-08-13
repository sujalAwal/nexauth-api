"""Master Data Response Schemas - Output format for master_data endpoints"""
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional


class MasterDataResponse(BaseModel):
    """Schema for master data response"""
    id: UUID
    name: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    
    class Config:
        from_attributes = True


class MasterDataDetailResponse(MasterDataResponse):
    """Extended response with deletion info for detail endpoints"""
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[UUID] = None
    

class MasterDataCollectionResponse(BaseModel):
    """Schema for master data collection response"""
    data: Optional[list[MasterDataResponse]] = None
