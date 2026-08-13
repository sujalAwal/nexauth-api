from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.modules.settings.models.setting import Setting


class SettingPublicService:
    """Service for public setting operations (read-only)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_active_settings(self) -> list[Setting]:
        query = select(Setting).where(Setting.is_active == True)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_settings_by_group(self, setting_group_id: UUID) -> list[Setting]:
        query = select(Setting).where(
            Setting.setting_group_id == setting_group_id,
            Setting.is_active == True,
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_setting_by_name(self, name: str) -> Setting | None:
        query = select(Setting).where(Setting.name == name, Setting.is_active == True)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
