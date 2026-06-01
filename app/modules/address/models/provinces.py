# app/modules/province/model.py
from sqlalchemy import Column, String, Integer, DateTime, Boolean, text, ForeignKey, Index
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER, BIT
from sqlalchemy.orm import relationship
from app.database import Base

class Province(Base):
    __tablename__ = 'provinces'
    
    id = Column(
        UNIQUEIDENTIFIER, 
        primary_key=True, 
        server_default=text('NEWID()')
    )
    name = Column(String(100), nullable=False)
    display_name = Column(String(100), nullable=False)
    code = Column(String(10), nullable=False)
    is_active = Column(Boolean, nullable=False, server_default=text('1'))
    created_at = Column(DateTime, nullable=False, server_default=text('GETDATE()'))
    updated_at = Column(DateTime, nullable=False, server_default=text('GETDATE()'), onupdate=text('GETDATE()'))
    deleted_at = Column(DateTime, nullable=True)
    country_id = Column(UNIQUEIDENTIFIER, ForeignKey('countries.id'), nullable=False)
    name_np = Column(String(100), nullable=True)
    province_order = Column(Integer, nullable=False)
    status = Column(BIT, nullable=False, server_default=text('1'))
    created_by_id = Column(UNIQUEIDENTIFIER, nullable=True)
    updated_by_id = Column(UNIQUEIDENTIFIER, nullable=True)
    deleted_by_id = Column(UNIQUEIDENTIFIER, nullable=True)
    
    # Relationships
    country = relationship("Country", backref="provinces")
    districts = relationship("District", back_populates="province")
    
    # ⚠️ ADD THESE INDEXES (matches your database)
    __table_args__ = (
        Index('IX_provinces_code', 'code'),
        Index('IX_provinces_country_id', 'country_id'),
    )