from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy import Column, String, Integer, DateTime, Boolean
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from app.database import Base
from app.utils.soft_delete import SoftDeleteMixin


class Category(Base, SoftDeleteMixin):
    """Category model for product/service categorization with display controls."""
    
    __tablename__ = "categories"
    __table_args__ = {"schema": "dbo"}
    
    id = Column(UNIQUEIDENTIFIER, primary_key=True, default=lambda: UUID(int=0))
    
    # Core category information
    title = Column(String(150), nullable=False)
    name = Column(String(150), nullable=False, unique=True, index=True)  # URL slug
    icon = Column(String(500), nullable=True)  # Icon/thumbnail for category grid
    description = Column(String, nullable=True)  # NVARCHAR(MAX)
    
    # Display & Ordering Controls
    display_order = Column(Integer, nullable=False, default=0, index=True)  # Sort order
    is_featured = Column(Boolean, nullable=False, default=False, index=True)  # Homepage banner
    
    # Status
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    deleted_at = Column(DateTime, nullable=True, index=True)
    
    # Audit tracking (UUIDs without FK constraints)
    created_by = Column(String(36), nullable=False)  # UUID as string
    updated_by = Column(String(36), nullable=False)  # UUID as string
    deleted_by = Column(String(36), nullable=True)   # UUID as string
    
    def __repr__(self):
        return f"<Category(id={self.id}, name={self.name}, title={self.title}, is_active={self.is_active})>"
