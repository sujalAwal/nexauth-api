from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.brands.models.brand import Brand


class BrandPublicService:
    """Service for public brand operations (read-only)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_active_brands(self) -> list[Brand]:
        query = select(Brand).where(Brand.is_active == True)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_brand_by_name(self, name: str) -> Brand | None:
        query = select(Brand).where(Brand.name == name, Brand.is_active == True)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
