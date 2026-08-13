"""SettingGroup Repository - Database access layer"""
from datetime import datetime, timezone
from sqlalchemy import select, exists as sa_exists
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.modules.setting_groups.models.setting_group import SettingGroup


class SettingGroupRepository:
    """Handles all database operations for setting groups"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, group_id: UUID) -> SettingGroup | None:
        result = await self.db.execute(select(SettingGroup).where(SettingGroup.id == group_id))
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> SettingGroup | None:
        result = await self.db.execute(select(SettingGroup).where(SettingGroup.name == name))
        return result.scalar_one_or_none()

    async def name_exists(self, name: str) -> bool:
        inner = select(SettingGroup.id).where(SettingGroup.name == name)
        result = await self.db.execute(select(inner.exists()))
        return result.scalar()

    async def get_all_active(self) -> list[SettingGroup]:
        query = select(SettingGroup).where(SettingGroup.is_active == True)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create(self, group: SettingGroup) -> SettingGroup:
        self.db.add(group)
        await self.db.commit()
        await self.db.refresh(group)
        return group

    async def update(self, group: SettingGroup) -> SettingGroup:
        self.db.add(group)
        await self.db.commit()
        await self.db.refresh(group)
        return group

    async def delete(self, group_id: UUID) -> bool:
        group = await self.get_by_id(group_id)
        if group:
            group.deleted_at = datetime.now(timezone.utc)
            self.db.add(group)
            await self.db.commit()
            return True
        return False
