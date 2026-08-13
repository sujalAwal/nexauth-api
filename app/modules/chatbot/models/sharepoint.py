from sqlalchemy import Column, Integer, String, Boolean, DateTime, BigInteger
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base
from app.utils.models.mixin.audit import AuditMixin
from app.utils.models.mixin.soft_delete import SoftDeleteMixin
from app.database import Base

class Sharepoint(Base, SoftDeleteMixin, AuditMixin):
    __tablename__ = "sharepoints"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    uuid = Column(String(255), nullable=False)
    url = Column(String(255), nullable=False)
    department = Column(String(100), nullable=True)
    content_hash = Column(String(64), nullable=True)
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    last_modified_at = Column(DateTime(timezone=True), nullable=True)
    file_created_at = Column(DateTime(timezone=True), nullable=True)  # ← typo fixed
    file_size = Column(BigInteger, nullable=True)
    enable_sync = Column(Boolean, default=True, nullable=False)
    data = Column(JSONB, nullable=True)
    is_file = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), nullable=True)