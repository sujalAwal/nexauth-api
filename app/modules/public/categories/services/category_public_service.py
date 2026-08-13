from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.categories.models.category import Category


class CategoryPublicService:
    """Service for public category operations (read-only)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_active_categories(self) -> list[Category]:
        query = (
            select(Category)
            .where(Category.is_active == True)
            .order_by(Category.display_order)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_category_by_name(self, name: str) -> Category | None:
        query = select(Category).where(Category.name == name, Category.is_active == True)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_featured_categories(self) -> list[Category]:
        query = (
            select(Category)
            .where(Category.is_featured == True, Category.is_active == True)
            .order_by(Category.display_order)
        )
        result = await self.db.execute(query)
        return result.scalars().all()
