from sqlalchemy.orm import Session
from uuid import UUID
from app.modules.settings.models.setting import Setting


class SettingPublicService:
    """Service for public setting operations (read-only)."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_active_settings(self) -> list[Setting]:
        """Get all active settings for public display."""
        return self.db.query(Setting).filter(Setting.is_active == True).all()
    
    def get_settings_by_group(self, setting_group_id: UUID) -> list[Setting]:
        """Get all settings in a group."""
        return self.db.query(Setting).filter(
            Setting.setting_group_id == setting_group_id,
            Setting.is_active == True
        ).all()
    
    def get_setting_by_name(self, name: str) -> Setting | None:
        """Get setting by name."""
        return self.db.query(Setting).filter(
            Setting.name == name,
            Setting.is_active == True
        ).first()
