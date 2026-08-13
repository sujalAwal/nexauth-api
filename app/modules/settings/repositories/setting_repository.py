"""Setting Repository - Database access layer"""
from datetime import datetime, timezone
from sqlalchemy import select, exists as sa_exists
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.modules.settings.models.setting import Setting


class SettingRepository:
    """Handles all database operations for settings"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, setting_id: UUID) -> Setting | None:
        result = await self.db.execute(select(Setting).where(Setting.id == setting_id))
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Setting | None:
        result = await self.db.execute(select(Setting).where(Setting.name == name))
        return result.scalar_one_or_none()

    async def name_exists(self, name: str) -> bool:
        inner = select(Setting.id).where(Setting.name == name)
        result = await self.db.execute(select(inner.exists()))
        return result.scalar()

    async def get_by_group_id(self, group_id: UUID) -> list[Setting]:
        query = select(Setting).where(Setting.setting_group_id == group_id)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_active_by_group(self, group_id: UUID) -> list[Setting]:
        query = select(Setting).where(
            Setting.setting_group_id == group_id,
            Setting.is_active == True,
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create(self, setting: Setting) -> Setting:
        self.db.add(setting)
        await self.db.commit()
        await self.db.refresh(setting)
        return setting

    async def update(self, setting: Setting) -> Setting:
        self.db.add(setting)
        await self.db.commit()
        await self.db.refresh(setting)
        return setting

    async def delete(self, setting_id: UUID) -> bool:
        setting = await self.get_by_id(setting_id)
        if setting:
            setting.deleted_at = datetime.now(timezone.utc)
            self.db.add(setting)
            await self.db.commit()
            return True
        return False
