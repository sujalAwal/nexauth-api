"""Tenant Response Schemas - Output format for tenant endpoints"""
from pydantic import BaseModel, field_validator
from uuid import UUID
from datetime import datetime
from typing import Optional
from app.utils.enums.plan_tier import PlanTier


class TenantResponse(BaseModel):
    """Schema for tenant response"""
    id: UUID
    name: str
    slug: str
    code: int
    plan_tier: PlanTier
    contact_email: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    domain: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    
    class Config:
        from_attributes = True
        use_enum_values = True


class TenantDetailResponse(TenantResponse):
    """Extended response with deletion info for detail endpoints"""
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[UUID] = None
    

class TenantCollectionResponse(BaseModel):
    """Schema for tenant collection response"""
    data: Optional[list[TenantResponse]] = None
