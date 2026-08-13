"""Tenant Request Schemas - Input validation for tenant endpoints"""
from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict
from typing import Optional
from app.utils.enums.plan_tier import PlanTier
from app.utils.enums.industry import Industry


class TenantCreateRequest(BaseModel):
    """Schema for creating a new tenant - code and slug are auto-generated"""
    model_config = ConfigDict(use_enum_values=True)

    name: str = Field(..., min_length=1, max_length=255, description="Unique tenant name")
    plan_tier: PlanTier = Field(description="Subscription plan tier")
    contact_email: Optional[EmailStr] = Field(None, description="Contact email address")
    industry: Optional[Industry] = Field(None, description="Industry classification")
    description: Optional[str] = Field(None, max_length=255, description="Tenant description")
    domain: Optional[str] = Field(
        None,
        max_length=255,
        description="Optional tenant domain/URL (e.g. https://acme.example.com)",
    )

    @field_validator("name")
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Tenant name cannot be empty")
        return v.strip()

    @field_validator("domain")
    def validate_domain(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        cleaned = v.strip()
        if not cleaned:
            return None
        # Accept bare domains or full URLs; normalize empty to None
        return cleaned


class TenantUpdateRequest(BaseModel):
    """Schema for updating an existing tenant"""
    # use_enum_values=True ensures the string value (e.g. "Pro") is passed to
    # SQLAlchemy instead of the enum object, preventing DB driver type errors.
    model_config = ConfigDict(use_enum_values=True)

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    plan_tier: Optional[PlanTier] = Field(None)
    contact_email: Optional[EmailStr] = None
    industry: Optional[Industry] = Field(None)   # max_length removed — irrelevant on Enum
    description: Optional[str] = Field(None, max_length=255)
    domain: Optional[str] = Field(
        None,
        max_length=255,
        description="Optional tenant domain/URL",
    )
    is_active: Optional[bool] = None

    @field_validator("name")
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Tenant name cannot be empty")
        return cleaned

    @field_validator("domain")
    def validate_domain(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        cleaned = v.strip()
        return cleaned or None
