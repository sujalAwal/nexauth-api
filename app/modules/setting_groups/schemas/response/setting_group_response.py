"""SettingGroup Response Schemas"""
from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime


class SettingGroupResponse(BaseModel):
    """Response schema for a single setting group"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    title: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class SettingGroupCollection(BaseModel):
    """Response schema for multiple setting groups"""
    groups: list[SettingGroupResponse]
