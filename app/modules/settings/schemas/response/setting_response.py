"""Setting Response Schemas"""
from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime
from app.utils.enums.setting_type_enum import SettingTypeEnum


class SettingResponse(BaseModel):
    """Response schema for a single setting"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    title: str
    description: Optional[str] = None
    type: SettingTypeEnum
    value: Optional[str] = None
    setting_group_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime


class SettingCollection(BaseModel):
    """Response schema for multiple settings"""
    settings: list[SettingResponse]
