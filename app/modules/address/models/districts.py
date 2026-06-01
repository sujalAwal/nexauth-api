# app/modules/district/model.py
from sqlalchemy import Column, String, Integer, DateTime, Boolean, text, ForeignKey, Index
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.orm import relationship
from app.database import Base

class District(Base):
    __tablename__ = 'districts'
    
    id = Column(UNIQUEIDENTIFIER, primary_key=True)
    name = Column(String(100), nullable=False)
    display_name = Column(String(100), nullable=False)
    code = Column(String(10), nullable=False)
    is_active = Column(Boolean, nullable=False, server_default=text('1'))
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    province_id = Column(UNIQUEIDENTIFIER, ForeignKey('provinces.id'), nullable=False)
    name_np = Column(String(100), nullable=True)
    district_code = Column(Integer, nullable=True)
    created_by_id = Column(UNIQUEIDENTIFIER, nullable=True)
    updated_by_id = Column(UNIQUEIDENTIFIER, nullable=True)
    deleted_by_id = Column(UNIQUEIDENTIFIER, nullable=True)
    
    # Relationships
    province = relationship("Province", back_populates="districts")
    
    # ⚠️ ADD THIS INDEX (matches your database)
    __table_args__ = (
        Index('IX_districts_province_id', 'province_id'),
    )