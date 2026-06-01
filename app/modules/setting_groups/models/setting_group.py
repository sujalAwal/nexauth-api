"""SettingGroup Model - Groups that contain related settings"""
from sqlalchemy import Column, String, DateTime, Boolean, text
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from datetime import datetime, timezone
from app.database import Base
from app.utils.models.mixin.soft_delete import SoftDeleteMixin


class SettingGroup(Base,SoftDeleteMixin):
    __tablename__ = 'setting_groups'
    
    id = Column(
        UNIQUEIDENTIFIER, 
        primary_key=True, 
        server_default=text('NEWID()')
    )
    name = Column(String(100), nullable=False, unique=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(String(500), nullable=True)
    is_active = Column(Boolean, nullable=False, server_default=text('1'))
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))  # ✅ Python sets this
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))  # ✅ Python sets this
    deleted_at = Column(DateTime, nullable=True, index=True)