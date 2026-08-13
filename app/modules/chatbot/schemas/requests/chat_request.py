from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SharepointIndexRequest(BaseModel):
    department: str = Field(..., description="Department for which to index SharePoint content")


class ChatRequest(BaseModel):
    user_id: UUID = Field(..., description="Unique identifier for the user")
    question: str = Field(..., min_length=1, description="User question")
    department: str = Field(default="general", description="Department scope")
    conversation_id: Optional[UUID] = Field(
        default=None,
        description="Existing conversation ID for follow-up questions",
    )


class ChatFeedbackRequest(BaseModel):
    user_id: UUID = Field(..., description="Unique identifier for the user")
    conversation_id: UUID = Field(..., description="Conversation the feedback belongs to")
    rating: int = Field(..., ge=1, le=5, description="Rating between 1 and 5")
    message: Optional[str] = Field(default=None, description="Optional feedback message")