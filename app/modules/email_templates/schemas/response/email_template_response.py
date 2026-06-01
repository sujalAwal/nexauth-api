"""EmailTemplate Response Schemas"""
from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime


class EmailTemplateResponse(BaseModel):
    """Response schema for a single email template"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    title: str
    name: str
    subject: str
    body: str
    cc: Optional[str] = None
    admin_subject: str
    admin_body: str
    admin_cc: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: UUID
    updated_by: UUID
    deleted_by: Optional[UUID] = None


class EmailTemplateCollection(BaseModel):
    """Response schema for multiple email templates"""
    templates: list[EmailTemplateResponse]
