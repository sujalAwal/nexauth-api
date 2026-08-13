from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from uuid import UUID


class SettingPublicResponse(BaseModel):
    """Public schema for setting response (customer-facing)."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    title: str
    description: Optional[str] = None
    value: str
    type: str
    setting_group_id: UUID


class SettingPublicCollection(BaseModel):
    """Collection of public settings."""
    
    data: List[SettingPublicResponse]
