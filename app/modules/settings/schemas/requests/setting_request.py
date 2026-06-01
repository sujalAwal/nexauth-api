"""Setting Request Schemas"""
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from app.utils.enums.setting_type_enum import SettingTypeEnum


class SettingRequest(BaseModel):
    """Base schema for Setting common fields"""
    
    name: str = Field(..., min_length=1, max_length=100, description="Unique setting name")
    title: str = Field(..., min_length=1, max_length=200, description="Display title")
    description: Optional[str] = Field(None, max_length=500, description="Setting description")
    type: SettingTypeEnum = Field(..., description="HTML input type for this setting")
    value: Optional[str] = Field(None, max_length=2000, description="Setting value (JSON or plain text)")
    setting_group_id: UUID = Field(..., description="ID of the setting group this belongs to")


class SettingCreateRequest(SettingRequest):
    """Schema for creating a new setting"""
    pass


class SettingUpdateRequest(SettingRequest):
    """Schema for updating an existing setting"""
    is_active: Optional[bool] = Field(None, description="Whether the setting is active")
