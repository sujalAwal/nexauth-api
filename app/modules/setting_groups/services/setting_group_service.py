"""SettingGroup Service - Business logic layer"""
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
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

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = SettingGroupRepository(db)
        self.query_handler = PaginationQueryHandler(db)

    async def create_setting_group(self, request: SettingGroupCreateRequest) -> SettingGroupResponse:
        if await self.repo.name_exists(request.name):
            raise ValueError(f"Setting group name '{request.name}' already exists")

        new_group = SettingGroup(
            name=request.name,
            title=request.title,
            description=request.description,
            is_active=True,
        )

        created_group = await self.repo.create(new_group)
        return SettingGroupResponse.model_validate(created_group)

    async def get_setting_group_by_id(self, group_id: UUID) -> SettingGroupResponse | None:
        group = await self.repo.get_by_id(group_id)
        if group:
            return SettingGroupResponse.model_validate(group)
        return None

    async def update_setting_group(self, group_id: UUID, request: SettingGroupUpdateRequest) -> SettingGroupResponse:
        group = await self.repo.get_by_id(group_id)
        if not group:
            raise ValueError(f"Setting group not found with ID: {group_id}")

        if request.name != group.name and await self.repo.name_exists(request.name):
            raise ValueError(f"Setting group name '{request.name}' already exists")

        group.name = request.name
        group.title = request.title
        group.description = request.description
        if request.is_active is not None:
            group.is_active = request.is_active

        updated_group = await self.repo.update(group)
        return SettingGroupResponse.model_validate(updated_group)

    async def delete_setting_group(self, group_id: UUID) -> bool:
        if not await self.repo.delete(group_id):
            raise ValueError(f"Setting group not found with ID: {group_id}")
        return True

    async def get_setting_groups_paginated(self, params: ListRequestFilters) -> dict:
        result = await self.query_handler.execute_paginated_query(
            query=select(SettingGroup),
            model=SettingGroup,
            params=params,
            searchable_fields=[SettingGroup.name, SettingGroup.title],
            sortable_fields=["created_at", "updated_at", "name"],
        )

        groups = [SettingGroupResponse.model_validate(group) for group in result.data]

        return {"data": groups, "pagination": result.pagination}
