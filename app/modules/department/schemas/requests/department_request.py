from pydantic import BaseModel, Field, field_validator
from typing import Optional


class DepartmentSharepointLinkRequest(BaseModel):
    sharepoint_url: str = Field(..., min_length=1, max_length=1000)
    label: Optional[str] = Field(None, max_length=255)
    sync_enabled: bool = True

    @field_validator("sharepoint_url")
    def normalize_sharepoint_url(cls, value: str) -> str:
        return value.strip()


class DepartmentCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: bool = True
    sharepoint_links: list[DepartmentSharepointLinkRequest] = Field(default_factory=list)

    @field_validator("name", "slug")
    def normalize_text_fields(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Field cannot be empty")
        return cleaned


class DepartmentUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    slug: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    sharepoint_links: Optional[list[DepartmentSharepointLinkRequest]] = None

    @field_validator("name", "slug")
    def normalize_optional_text_fields(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Field cannot be empty")
        return cleaned
