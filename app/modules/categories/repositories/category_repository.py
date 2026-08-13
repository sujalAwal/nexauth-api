from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime, timezone
from app.modules.categories.models.category import Category


class CategoryRepository:
    """Repository for category database operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, category_id: UUID) -> Category | None:
        result = await self.db.execute(select(Category).where(Category.id == category_id))
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Category | None:
        result = await self.db.execute(select(Category).where(Category.name == name))
        return result.scalar_one_or_none()

    async def name_exists(self, name: str, exclude_id: UUID = None) -> bool:
        inner = select(Category.id).where(Category.name == name)
        if exclude_id:
            inner = inner.where(Category.id != exclude_id)
        result = await self.db.execute(select(inner.exists()))
        return result.scalar()

    async def get_all_active(self) -> list[Category]:
        query = select(Category).where(Category.is_active == True).order_by(Category.display_order)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_featured(self) -> list[Category]:
        query = (
            select(Category)
            .where(Category.is_featured == True, Category.is_active == True)
            .order_by(Category.display_order)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create(self, category_data: dict) -> Category:
        category = Category(**category_data)
        self.db.add(category)
        await self.db.commit()
        await self.db.refresh(category)
        return category

    async def update(self, category_id: UUID, category_data: dict) -> Category | None:
        category = await self.get_by_id(category_id)
        if not category:
            return None

        for key, value in category_data.items():
            if value is not None and hasattr(category, key):
                setattr(category, key, value)

        self.db.add(category)
        await self.db.commit()
        await self.db.refresh(category)
        return category

    async def delete(self, category_id: UUID, deleted_by: UUID) -> Category | None:
        category = await self.get_by_id(category_id)
        if not category:
            return None

        category.deleted_at = datetime.now(timezone.utc)
        category.deleted_by = deleted_by

        self.db.add(category)
        await self.db.commit()
        await self.db.refresh(category)
        return category

    async def get_all(self, skip: int = 0, limit: int = 10) -> list[Category]:
        query = select(Category).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def count(self) -> int:
        query = select(func.count(Category.id))
        result = await self.db.execute(query)
        return result.scalar_one()
