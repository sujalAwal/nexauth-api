from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ChatResponse(BaseModel):
    conversation_id: UUID
    answer: str
    citations: List[str] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)
    relevant_chunks: int
    retrieval_fallback: bool = False
    provider: str
    model: str
    tokens_used: int


class SyncStats(BaseModel):
    total_found: int = 0
    new: int = 0
    updated: int = 0
    deleted: int = 0
    failed: int = 0
    skipped: int = 0
    details: List[dict] = Field(default_factory=list)


class SyncResponse(BaseModel):
    status: str
    message: str = ""
    stats: SyncStats = Field(default_factory=SyncStats)


class SyncJobInfo(BaseModel):
    job_id: Optional[str] = None
    job_status: Optional[str] = None
    job_started_at: Optional[str] = None
    job_finished_at: Optional[str] = None
    job_error: Optional[str] = None


class SyncStatusResponse(BaseModel):
    total_documents: int = 0
    failed_documents: int = 0
    total_chunks: int = 0
    last_sync: datetime
    last_job: SyncJobInfo = Field(default_factory=SyncJobInfo)


class ChatStreamEvent(BaseModel):
    type: str
    data: dict = Field(default_factory=dict)


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: Optional[str] = None
    department: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ConversationCollection(BaseModel):
    conversations: List[ConversationResponse] = Field(default_factory=list)


class FeedbackResponse(BaseModel):
    id: UUID
    user_id: UUID
    conversation_id: UUID
    rating: int
    message: Optional[str] = None
    created_at: Optional[datetime] = None