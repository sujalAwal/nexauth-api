"""EmailTemplate Model - Email template management"""
from sqlalchemy import Column, String, DateTime, Boolean, text
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from app.database import Base


class EmailTemplate(Base):
    __tablename__ = 'email_templates'
    
    id = Column(
        UNIQUEIDENTIFIER,
        primary_key=True,
        server_default=text('NEWID()')
    )
    title = Column(String(200), nullable=False)
    name = Column(String(100), nullable=False, unique=True, index=True)
    subject = Column(String(300), nullable=False)
    body = Column(String(5000), nullable=False)
    cc = Column(String(500), nullable=True)  # Comma-separated emails
    admin_subject = Column(String(300), nullable=False)
    admin_body = Column(String(5000), nullable=False)
    admin_cc = Column(String(500), nullable=True)  # Comma-separated emails
    is_active = Column(Boolean, nullable=False, server_default=text('1'))
    created_at = Column(DateTime, nullable=False, server_default=text('GETDATE()'))
    updated_at = Column(DateTime, nullable=False, server_default=text('GETDATE()'), onupdate=text('GETDATE()'))
    deleted_at = Column(DateTime, nullable=True, index=True)
    created_by = Column(UNIQUEIDENTIFIER, nullable=False)
    updated_by = Column(UNIQUEIDENTIFIER, nullable=False)
    deleted_by = Column(UNIQUEIDENTIFIER, nullable=True)
