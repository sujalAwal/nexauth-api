"""SettingGroup Request Schemas"""
from pydantic import BaseModel, Field
from typing import Optional


class SettingGroupRequest(BaseModel):
    """Base schema for SettingGroup common fields"""
    
    name: str = Field(..., min_length=1, max_length=100, description="Unique group name")
    title: str = Field(..., min_length=1, max_length=200, description="Display title")
    description: Optional[str] = Field(None, max_length=500, description="Group description")


class SettingGroupCreateRequest(SettingGroupRequest):
    """Schema for creating a new setting group"""
    pass


class SettingGroupUpdateRequest(SettingGroupRequest):
    """Schema for updating an existing setting group"""
    is_active: Optional[bool] = Field(None, description="Whether the group is active")
