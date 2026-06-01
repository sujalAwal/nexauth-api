"""Setting Repository - Database access layer"""
from sqlalchemy.orm import Session
from uuid import UUID
from app.modules.settings.models.setting import Setting


class SettingRepository:
    """Handles all database operations for settings"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, setting_id: UUID) -> Setting | None:
        """Retrieve a setting by ID"""
        return self.db.query(Setting).filter(Setting.id == setting_id).first()
    
    def get_by_name(self, name: str) -> Setting | None:
        """Retrieve a setting by name"""
        return self.db.query(Setting).filter(Setting.name == name).first()
    
    def name_exists(self, name: str) -> bool:
        """Check if a name already exists"""
        return self.db.query(Setting).filter(Setting.name == name).exists().scalar()
    
    def get_by_group_id(self, group_id: UUID) -> list[Setting]:
        """Retrieve all settings for a group"""
        return self.db.query(Setting).filter(Setting.setting_group_id == group_id).all()
    
    def get_active_by_group(self, group_id: UUID) -> list[Setting]:
        """Retrieve active settings for a group"""
        return self.db.query(Setting).filter(
            Setting.setting_group_id == group_id,
            Setting.is_active == True
        ).all()
    
    def create(self, setting: Setting) -> Setting:
        """Create a new setting"""
        self.db.add(setting)
        self.db.commit()
        self.db.refresh(setting)
        return setting
    
    def update(self, setting: Setting) -> Setting:
        """Update an existing setting"""
        self.db.commit()
        self.db.refresh(setting)
        return setting
    
    def delete(self, setting_id: UUID) -> bool:
        """Soft delete a setting"""
        setting = self.get_by_id(setting_id)
        if setting:
            setting.deleted_at = datetime.now(timezone.utc)
            self.db.commit()
            return True
        return False
