from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, Float, ForeignKey, CheckConstraint, UniqueConstraint, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector  # pyright: ignore[reportMissingImports]
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base
from app.utils.models.mixin.audit import AuditMixin
from app.utils.models.mixin.soft_delete import SoftDeleteMixin


class Document(Base, SoftDeleteMixin, AuditMixin):
    __tablename__ = "documents"
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'processing', 'completed', 'failed')", name="ck_documents_status")
    ),

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_type = Column(String(20), nullable=False, default="sharepoint")
    file_path = Column(String(1000), unique=True, nullable=False)
    filename = Column(String(255), nullable=False)
    department = Column(String(100), nullable=False)
    content_hash = Column(String(64), nullable=False)
    file_size = Column(BigInteger)
    file_type = Column(String(50))
    status = Column(String(20), default="pending")
    error_message = Column(Text)
    chunk_count = Column(Integer, default=0)
    uuid = Column(String(255), nullable=True)
    url = Column(String(1000), nullable=True)
    web_url = Column(Text, nullable=True)
    last_modified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base, SoftDeleteMixin, AuditMixin):
    __tablename__ = "document_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"))
    chunk_text = Column(Text, nullable=True)
    content_preview = Column(String(300), nullable=True)
    embedding = Column(Vector(1536))
    chunk_index = Column(Integer, nullable=False)
    department = Column(String(100), nullable=False)
    source_file = Column(String(500))
    url = Column(String(1000), nullable=True)
    content_hash = Column(String(64), nullable=True)
    chunk_metadata = Column(JSONB, nullable=True)
    token_count = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    document = relationship("Document", back_populates="chunks")


class Conversation(Base, SoftDeleteMixin, AuditMixin):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    title = Column(String(255))
    department = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    feedbacks = relationship("ChatFeedback", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base, SoftDeleteMixin, AuditMixin):
    __tablename__ = "messages"
    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant', 'system')", name="ck_messages_role"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"))
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    citations = Column(JSONB)
    tokens_used = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    conversation = relationship("Conversation", back_populates="messages")


class ChatFeedback(Base, SoftDeleteMixin, AuditMixin):
    __tablename__ = "chat_feedbacks"
    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_chat_feedbacks_rating"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"))
    rating = Column(Integer, nullable=False)
    message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    conversation = relationship("Conversation", back_populates="feedbacks")


class SyncJob(Base, SoftDeleteMixin, AuditMixin):
    __tablename__ = "sync_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(String(20), nullable=False, default="pending")
    stats = Column(JSONB)
    error = Column(Text)
    started_at = Column(DateTime(timezone=True))
    finished_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())