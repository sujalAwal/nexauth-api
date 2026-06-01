

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, ConfigDict


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    email: EmailStr
    phone_number: Optional[str] = None
    country_code: str
    state: Optional[str] = None
    city: Optional[str] = None
    municipality: Optional[str] = None
    address: Optional[str] = None
    postal_code: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime