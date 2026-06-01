"""Setting Service - Business logic layer"""
from uuid import UUID
from sqlalchemy.orm import Session
from app.modules.settings.models.setting import Setting
from app.modules.settings.schemas.requests.setting_request import (
    SettingCreateRequest,
    SettingUpdateRequest,
)
from app.modules.settings.schemas.response.setting_response import SettingResponse
from app.modules.settings.repositories.setting_repository import SettingRepository
from app.modules.setting_groups.repositories.setting_group_repository import SettingGroupRepository
from app.schemas.request import ListRequestFilters
from app.utils.models.mixin.pagination_query_handler import PaginationQueryHandler


class SettingService:
    """Handles business logic for setting operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = SettingRepository(db)
        self.group_repo = SettingGroupRepository(db)
        self.query_handler = PaginationQueryHandler()
    
    def create_setting(self, request: SettingCreateRequest) -> SettingResponse:
        """Create a new setting"""
        # Validate setting group exists
        group = self.group_repo.get_by_id(request.setting_group_id)
        if not group:
            raise ValueError(f"Setting group not found with ID: {request.setting_group_id}")
        
        # Validate unique name
        if self.repo.name_exists(request.name):
            raise ValueError(f"Setting name '{request.name}' already exists")
        
        new_setting = Setting(
            name=request.name,
            title=request.title,
            description=request.description,
            type=request.type,
            value=request.value,
            setting_group_id=request.setting_group_id,
            is_active=True
        )
        
        created_setting = self.repo.create(new_setting)
        return SettingResponse.model_validate(created_setting)
    
    def get_setting_by_id(self, setting_id: UUID) -> SettingResponse | None:
        """Retrieve a setting by ID"""
        setting = self.repo.get_by_id(setting_id)
        if setting:
            return SettingResponse.model_validate(setting)
        return None
    
    def update_setting(self, setting_id: UUID, request: SettingUpdateRequest) -> SettingResponse:
        """Update an existing setting"""
        setting = self.repo.get_by_id(setting_id)
        if not setting:
            raise ValueError(f"Setting not found with ID: {setting_id}")
        
        # Validate setting group exists (if changed)
        if request.setting_group_id != setting.setting_group_id:
            group = self.group_repo.get_by_id(request.setting_group_id)
            if not group:
                raise ValueError(f"Setting group not found with ID: {request.setting_group_id}")
        
        # Check if new name is unique
        if request.name != setting.name and self.repo.name_exists(request.name):
            raise ValueError(f"Setting name '{request.name}' already exists")
        
        setting.name = request.name
        setting.title = request.title
        setting.description = request.description
        setting.type = request.type
        setting.value = request.value
        setting.setting_group_id = request.setting_group_id
        if request.is_active is not None:
            setting.is_active = request.is_active
        
        updated_setting = self.repo.update(setting)
        return SettingResponse.model_validate(updated_setting)
    
    def delete_setting(self, setting_id: UUID) -> bool:
        """Delete (soft delete) a setting"""
        if not self.repo.delete(setting_id):
            raise ValueError(f"Setting not found with ID: {setting_id}")
        return True
    
    def get_settings_by_group(self, group_id: UUID) -> list[SettingResponse]:
        """Get all settings for a group"""
        # Verify group exists
        group = self.group_repo.get_by_id(group_id)
        if not group:
            raise ValueError(f"Setting group not found with ID: {group_id}")
        
        settings = self.repo.get_by_group_id(group_id)
        return [SettingResponse.model_validate(setting) for setting in settings]
    
    def get_settings_paginated(self, params: ListRequestFilters) -> dict:
        """Get paginated list of settings"""
        query = self.db.query(Setting)
        
        result = self.query_handler.execute_paginated_query(
            query=query,
            params=params,
            searchable_fields=[Setting.name, Setting.title],
            sortable_fields=["created_at", "updated_at", "name", "type"]
        )
        
        settings = [SettingResponse.model_validate(setting) for setting in result["data"]]
        
        return {
            "data": settings,
            "pagination": result["pagination"]
        }
