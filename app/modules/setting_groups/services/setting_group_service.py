"""SettingGroup Service - Business logic layer"""
from uuid import UUID
from sqlalchemy.orm import Session
from app.modules.setting_groups.models.setting_group import SettingGroup
from app.modules.setting_groups.schemas.requests.setting_group_request import (
    SettingGroupCreateRequest,
    SettingGroupUpdateRequest,
)
from app.modules.setting_groups.schemas.response.setting_group_response import SettingGroupResponse
from app.modules.setting_groups.repositories.setting_group_repository import SettingGroupRepository
from app.schemas.request import ListRequestFilters
from app.utils.models.mixin.pagination_query_handler import PaginationQueryHandler


class SettingGroupService:
    """Handles business logic for setting group operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = SettingGroupRepository(db)
        self.query_handler = PaginationQueryHandler()
    
    def create_setting_group(self, request: SettingGroupCreateRequest) -> SettingGroupResponse:
        """Create a new setting group"""
        # Validate unique name
        if self.repo.name_exists(request.name):
            raise ValueError(f"Setting group name '{request.name}' already exists")
        
        new_group = SettingGroup(
            name=request.name,
            title=request.title,
            description=request.description,
            is_active=True
        )
        
        created_group = self.repo.create(new_group)
        return SettingGroupResponse.model_validate(created_group)
    
    def get_setting_group_by_id(self, group_id: UUID) -> SettingGroupResponse | None:
        """Retrieve a setting group by ID"""
        group = self.repo.get_by_id(group_id)
        if group:
            return SettingGroupResponse.model_validate(group)
        return None
    
    def update_setting_group(self, group_id: UUID, request: SettingGroupUpdateRequest) -> SettingGroupResponse:
        """Update an existing setting group"""
        group = self.repo.get_by_id(group_id)
        if not group:
            raise ValueError(f"Setting group not found with ID: {group_id}")
        
        # Check if new name is unique
        if request.name != group.name and self.repo.name_exists(request.name):
            raise ValueError(f"Setting group name '{request.name}' already exists")
        
        group.name = request.name
        group.title = request.title
        group.description = request.description
        if request.is_active is not None:
            group.is_active = request.is_active
        
        updated_group = self.repo.update(group)
        return SettingGroupResponse.model_validate(updated_group)
    
    def delete_setting_group(self, group_id: UUID) -> bool:
        """Delete (soft delete) a setting group"""
        if not self.repo.delete(group_id):
            raise ValueError(f"Setting group not found with ID: {group_id}")
        return True
    
    def get_setting_groups_paginated(self, params: ListRequestFilters) -> dict:
        """Get paginated list of setting groups"""
        query = self.db.query(SettingGroup)
        
        result = self.query_handler.execute_paginated_query(
            query=query,
            params=params,
            searchable_fields=[SettingGroup.name, SettingGroup.title],
            sortable_fields=["created_at", "updated_at", "name"]
        )
        
        groups = [SettingGroupResponse.model_validate(group) for group in result["data"]]
        
        return {
            "data": groups,
            "pagination": result["pagination"]
        }
