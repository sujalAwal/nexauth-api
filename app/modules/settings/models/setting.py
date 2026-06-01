"""Setting Model - Individual settings with type and value"""
from sqlalchemy import Column, String, DateTime, Boolean, text, ForeignKey
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from app.database import Base


class Setting(Base):
    __tablename__ = 'settings'
    
    id = Column(
        UNIQUEIDENTIFIER, 
        primary_key=True, 
        server_default=text('NEWID()')
    )
    name = Column(String(100), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(String(500), nullable=True)
    type = Column(String(50), nullable=False)  # text, color, checkbox, textarea, select, etc.
    value = Column(String(2000), nullable=True)  # JSON or plain value
    setting_group_id = Column(UNIQUEIDENTIFIER, ForeignKey('setting_groups.id'), nullable=False)
    is_active = Column(Boolean, nullable=False, server_default=text('1'))
    created_at = Column(DateTime, nullable=False, server_default=text('GETDATE()'))
    updated_at = Column(DateTime, nullable=False, server_default=text('GETDATE()'), onupdate=text('GETDATE()'))
    deleted_at = Column(DateTime, nullable=True, index=True)
