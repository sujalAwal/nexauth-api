"""Master Data Items Request Schemas - Input validation for master_data_items endpoints"""
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
from uuid import UUID


class MasterDataItemCreateRequest(BaseModel):
    """Schema for creating a new master data item"""
    model_config = ConfigDict(use_enum_values=True)

    master_data_id: UUID = Field(..., description="Master data ID")
    name: str = Field(..., min_length=1, max_length=255, description="Master data item name")
    code: str = Field(..., min_length=1, max_length=255, description="Master data item code")
    description: Optional[str] = Field(None, max_length=255, description="Master data item description")

    @field_validator("name")
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Master data item name cannot be empty")
        return v.strip()
    
    @field_validator("code")
    def validate_code(cls, v):
        if not v or not v.strip():
            raise ValueError("Master data item code cannot be empty")
        return v.strip()


class MasterDataItemUpdateRequest(BaseModel):
    """Schema for updating an existing master data item"""
    model_config = ConfigDict(use_enum_values=True)

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    code: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None
