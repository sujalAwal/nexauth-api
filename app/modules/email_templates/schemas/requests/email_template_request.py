"""EmailTemplate Request Schemas"""
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID


class EmailTemplateRequest(BaseModel):
    """Base schema for EmailTemplate common fields"""
    
    title: str = Field(..., min_length=1, max_length=200, description="Display title")
    name: str = Field(..., min_length=1, max_length=100, description="Unique template name")
    subject: str = Field(..., min_length=1, max_length=300, description="Email subject for users")
    body: str = Field(..., min_length=1, max_length=5000, description="Email body for users")
    cc: Optional[str] = Field(None, max_length=500, description="CC recipients (comma-separated)")
    admin_subject: str = Field(..., min_length=1, max_length=300, description="Admin notification subject")
    admin_body: str = Field(..., min_length=1, max_length=5000, description="Admin notification body")
    admin_cc: Optional[str] = Field(None, max_length=500, description="Admin CC recipients (comma-separated)")


class EmailTemplateCreateRequest(EmailTemplateRequest):
    """Schema for creating a new email template"""
    created_by: UUID = Field(..., description="UUID of user creating the template")


class EmailTemplateUpdateRequest(EmailTemplateRequest):
    """Schema for updating an existing email template"""
    is_active: Optional[bool] = Field(None, description="Whether template is active")
    updated_by: UUID = Field(..., description="UUID of user updating the template")
