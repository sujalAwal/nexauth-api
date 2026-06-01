# app/modules/country/model.py
from sqlalchemy import Column, String, DateTime, Boolean, text ,CHAR
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from app.database import Base

class Country(Base):
    __tablename__ = 'countries'
    
    id = Column(
        UNIQUEIDENTIFIER, 
        primary_key=True, 
        server_default=text('NEWID()')
    )
    name = Column(String(200), nullable=False)
    display_name = Column(String(200), nullable=False)
    code = Column(CHAR(5), nullable=False, unique=True)  # ← CHAR, not String
    is_active = Column(Boolean, nullable=False, server_default=text('1'))
    created_at = Column(DateTime, nullable=False, server_default=text('GETDATE()'))
    updated_at = Column(DateTime, nullable=False, server_default=text('GETDATE()'), onupdate=text('GETDATE()'))
    deleted_at = Column(DateTime, nullable=True)