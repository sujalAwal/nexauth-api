"""SettingGroup Repository - Database access layer"""
from sqlalchemy import exists
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from uuid import UUID
from app.modules.setting_groups.models.setting_group import SettingGroup


class SettingGroupRepository:
    """Handles all database operations for setting groups"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, group_id: UUID) -> SettingGroup | None:
        """Retrieve a setting group by ID"""
        return self.db.query(SettingGroup).filter(SettingGroup.id == group_id).first()
    
    def get_by_name(self, name: str) -> SettingGroup | None:
        """Retrieve a setting group by name"""
        return self.db.query(SettingGroup).filter(SettingGroup.name == name).first()
    
    def name_exists(self, name: str) -> bool:
        return self.db.query(SettingGroup.name).where(SettingGroup.name == name).first() is not None
    
    def get_all_active(self) -> list[SettingGroup]:
        """Retrieve all active setting groups"""
        return self.db.query(SettingGroup).filter(SettingGroup.is_active == True).all()
    
    def create(self, group: SettingGroup) -> SettingGroup:
        """Create a new setting group"""
        self.db.add(group)
        self.db.commit()
        self.db.refresh(group)
        return group
    
    def update(self, group: SettingGroup) -> SettingGroup:
        """Update an existing setting group"""
        self.db.commit()
        self.db.refresh(group)
        return group
    
    def delete(self, group_id: UUID) -> bool:
        """Soft delete a setting group"""
        group = self.get_by_id(group_id)
        if group:
            group.deleted_at = datetime.now(timezone.utc)
            self.db.commit()
            return True
        return False
