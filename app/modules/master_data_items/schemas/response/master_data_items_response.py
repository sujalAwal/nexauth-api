"""Master Data Items Response Schemas - Output format for master_data_items endpoints"""
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional


class MasterDataItemResponse(BaseModel):
    """Schema for master data item response"""
    id: UUID
    master_data_id: UUID
    name: str
    code: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    
    class Config:
        from_attributes = True


class MasterDataItemDetailResponse(MasterDataItemResponse):
    """Extended response with deletion info for detail endpoints"""
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[UUID] = None
    

class MasterDataItemCollectionResponse(BaseModel):
    """Schema for master data items collection response"""
    data: Optional[list[MasterDataItemResponse]] = None
