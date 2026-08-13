"""Setting Service - Business logic layer"""
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
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

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = SettingRepository(db)
        self.group_repo = SettingGroupRepository(db)
        self.query_handler = PaginationQueryHandler(db)

    async def create_setting(self, request: SettingCreateRequest) -> SettingResponse:
        group = await self.group_repo.get_by_id(request.setting_group_id)
        if not group:
            raise ValueError(f"Setting group not found with ID: {request.setting_group_id}")

        if await self.repo.name_exists(request.name):
            raise ValueError(f"Setting name '{request.name}' already exists")

        new_setting = Setting(
            name=request.name,
            title=request.title,
            description=request.description,
            type=request.type,
            value=request.value,
            setting_group_id=request.setting_group_id,
            is_active=True,
        )

        created_setting = await self.repo.create(new_setting)
        return SettingResponse.model_validate(created_setting)

    async def get_setting_by_id(self, setting_id: UUID) -> SettingResponse | None:
        setting = await self.repo.get_by_id(setting_id)
        if setting:
            return SettingResponse.model_validate(setting)
        return None

    async def update_setting(self, setting_id: UUID, request: SettingUpdateRequest) -> SettingResponse:
        setting = await self.repo.get_by_id(setting_id)
        if not setting:
            raise ValueError(f"Setting not found with ID: {setting_id}")

        if request.setting_group_id != setting.setting_group_id:
            group = await self.group_repo.get_by_id(request.setting_group_id)
            if not group:
                raise ValueError(f"Setting group not found with ID: {request.setting_group_id}")

        if request.name != setting.name and await self.repo.name_exists(request.name):
            raise ValueError(f"Setting name '{request.name}' already exists")

        setting.name = request.name
        setting.title = request.title
        setting.description = request.description
        setting.type = request.type
        setting.value = request.value
        setting.setting_group_id = request.setting_group_id
        if request.is_active is not None:
            setting.is_active = request.is_active

        updated_setting = await self.repo.update(setting)
        return SettingResponse.model_validate(updated_setting)

    async def delete_setting(self, setting_id: UUID) -> bool:
        if not await self.repo.delete(setting_id):
            raise ValueError(f"Setting not found with ID: {setting_id}")
        return True

    async def get_settings_by_group(self, group_id: UUID) -> list[SettingResponse]:
        group = await self.group_repo.get_by_id(group_id)
        if not group:
            raise ValueError(f"Setting group not found with ID: {group_id}")

        settings = await self.repo.get_by_group_id(group_id)
        return [SettingResponse.model_validate(setting) for setting in settings]

    async def get_settings_paginated(self, params: ListRequestFilters) -> dict:
        result = await self.query_handler.execute_paginated_query(
            query=select(Setting),
            model=Setting,
            params=params,
            searchable_fields=[Setting.name, Setting.title],
            sortable_fields=["created_at", "updated_at", "name", "type"],
        )

        settings = [SettingResponse.model_validate(setting) for setting in result.data]

        return {"data": settings, "pagination": result.pagination}
