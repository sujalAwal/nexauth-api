"""Master Data Request Schemas - Input validation for master_data endpoints"""
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional


class MasterDataCreateRequest(BaseModel):
    """Schema for creating a new master data entry"""
    model_config = ConfigDict(use_enum_values=True)

    name: str = Field(..., min_length=1, max_length=255, description="Master data name")
    description: Optional[str] = Field(None, max_length=255, description="Master data description")

    @field_validator("name")
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Master data name cannot be empty")
        return v.strip()


class MasterDataUpdateRequest(BaseModel):
    """Schema for updating an existing master data entry"""
    model_config = ConfigDict(use_enum_values=True)

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None