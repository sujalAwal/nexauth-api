from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional


class UserRequest(BaseModel):
    """Base schema for user common fields"""
    
    email: EmailStr = Field(..., description="User's email address")
    name: str = Field(..., description="User's full name")
    first_name: str = Field(..., description="User's first name")
    middle_name: Optional[str] = Field(None, description="User's middle name")
    last_name: str = Field(..., description="User's last name")
    country: str = Field(..., description="User's country of residence")
    state: Optional[str] = Field(None, description="User's state of residence")
    city: Optional[str] = Field(None, description="User's city of residence")
    municipality: Optional[str] = Field(None, description="User's municipality of residence")
    postal_code: Optional[str] = Field(None, description="User's postal code")
    address: Optional[str] = Field(None, description="User's full address")
    phone_number: Optional[str] = Field(None, description="User's phone number")


class UserCreateRequest(UserRequest):
    """Schema for user creation requests - includes password"""
    
    password: str = Field(..., description="User's password (min 8 chars, must contain letter and digit)")
    
    @field_validator('password')
    def validate_password(cls, value):
        """Validate password strength"""
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(char.isdigit() for char in value):
            raise ValueError("Password must contain at least one digit")
        if not any(char.isalpha() for char in value):
            raise ValueError("Password must contain at least one letter")
        return value


class UserUpdateRequest(UserRequest):
    """Schema for user update requests - user_id comes from URL path, not body"""
    # Note: Do NOT include id field here. Use the user_id from the URL path instead.
    # This schema should only contain the fields that can be updated.
    pass

    