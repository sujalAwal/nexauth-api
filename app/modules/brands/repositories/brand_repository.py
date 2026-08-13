from sqlalchemy import func, select, exists as sa_exists
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime, timezone
from app.modules.brands.models.brand import Brand


class BrandRepository:
    """Repository for brand database operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, brand_id: UUID) -> Brand | None:
        result = await self.db.execute(select(Brand).where(Brand.id == brand_id))
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Brand | None:
        result = await self.db.execute(select(Brand).where(Brand.name == name))
        return result.scalar_one_or_none()

    async def name_exists(self, name: str, exclude_id: UUID = None) -> bool:
        inner = select(Brand.id).where(Brand.name == name)
        if exclude_id:
            inner = inner.where(Brand.id != exclude_id)
        result = await self.db.execute(select(inner.exists()))
        return result.scalar()

    async def get_all_active(self) -> list[Brand]:
        query = select(Brand).where(Brand.is_active == True)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_featured(self) -> list[Brand]:
        query = select(Brand).where(Brand.is_featured == True, Brand.is_active == True)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def increment_visit_count(self, brand_id: UUID) -> None:
        brand = await self.get_by_id(brand_id)
        if brand:
            brand.visit_count += 1
            self.db.add(brand)
            await self.db.commit()

    async def create(self, brand_data: dict) -> Brand:
        brand = Brand(**brand_data)
        self.db.add(brand)
        await self.db.commit()
        await self.db.refresh(brand)
        return brand

    async def update(self, brand_id: UUID, brand_data: dict) -> Brand | None:
        brand = await self.get_by_id(brand_id)
        if not brand:
            return None

        for key, value in brand_data.items():
            if value is not None and hasattr(brand, key):
                setattr(brand, key, value)

        self.db.add(brand)
        await self.db.commit()
        await self.db.refresh(brand)
        return brand

    async def delete(self, brand_id: UUID, deleted_by: UUID) -> Brand | None:
        brand = await self.get_by_id(brand_id)
        if not brand:
            return None

        brand.deleted_at = datetime.now(timezone.utc)
        brand.deleted_by = deleted_by

        self.db.add(brand)
        await self.db.commit()
        await self.db.refresh(brand)
        return brand

    async def get_all(self, skip: int = 0, limit: int = 10) -> list[Brand]:
        query = select(Brand).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def count(self) -> int:
        query = select(func.count(Brand.id))
        result = await self.db.execute(query)
        return result.scalar_one()
