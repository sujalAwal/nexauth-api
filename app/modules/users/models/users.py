# app/modules/user/model.py
from sqlalchemy import Column, String, DateTime, Boolean, text
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from app.database import Base

class User(Base):
    __tablename__ = 'users'
    
    id = Column(
        UNIQUEIDENTIFIER, 
        primary_key=True, 
        server_default=text('NEWID()')
    )
    name = Column(String(50), nullable=False)
    first_name = Column(String(50), nullable=False)
    middle_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=False)
    email = Column(String(100), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    phone_number = Column(String(20), nullable=True)
    country_code = Column(String(5), nullable=False)
    state = Column(String(5), nullable=True)
    city = Column(String(100), nullable=True)
    municipality = Column(String(100), nullable=True)
    address = Column(String(255), nullable=True)
    postal_code = Column(String(10), nullable=True)
    is_active = Column(Boolean, nullable=False, server_default=text('0'))
    created_at = Column(DateTime, nullable=False, server_default=text('GETDATE()'))
    updated_at = Column(DateTime, nullable=False, server_default=text('GETDATE()'), onupdate=text('GETDATE()'))
    deleted_at = Column(DateTime, nullable=True)
    email_verified_at = Column(DateTime, nullable=True)