from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy import Column, String, Integer, DateTime, Boolean
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from app.database import Base
from app.utils.soft_delete import SoftDeleteMixin


class Brand(Base, SoftDeleteMixin):
    """Brand model with corporate identity and analytics tracking."""
    
    __tablename__ = "brands"
    __table_args__ = {"schema": "dbo"}
    
    id = Column(UNIQUEIDENTIFIER, primary_key=True, default=lambda: UUID(int=0))
    
    # Core brand information
    name = Column(String(150), nullable=False, unique=True, index=True)
    title = Column(String(150), nullable=False)
    logo = Column(String(500), nullable=True)
    description = Column(String, nullable=True)  # NVARCHAR(MAX)
    
    # Corporate Identity & Heritage
    website_url = Column(String(255), nullable=True)
    country_of_origin = Column(String(100), nullable=True)
    founded_year = Column(Integer, nullable=True)
    
    # Analytics & Status
    visit_count = Column(Integer, nullable=False, default=0)
    is_featured = Column(Boolean, nullable=False, default=False)
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
        return f"<Brand(id={self.id}, name={self.name}, is_active={self.is_active})>"
