from pydantic import BaseModel, Field
from typing import Any, Optional, Generic, TypeVar
from datetime import datetime, timezone

from app.schemas.pagination_response import PaginationResponse

# Generic type for data
T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """General Response Format for the entire API"""
    
    success: bool = True
    message: str
    data: Optional[T] = None
    paginations : Optional[PaginationResponse] = None
    errors: Optional[Any] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    

    
# Common Response Types
class SuccessResponse(ApiResponse):
    """Simple success response without data"""
    success: bool = True
    message: str = "Operation successful"


class ErrorResponse(BaseModel):
    """Standard error response"""
    success: bool = False
    message: str
    errors: Optional[Any] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))