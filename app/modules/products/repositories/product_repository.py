from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime, timezone
from app.modules.products.models.product import Product


class ProductRepository:
    """Repository for product database operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, product_id: UUID) -> Product | None:
        result = await self.db.execute(select(Product).where(Product.id == product_id))
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Product | None:
        result = await self.db.execute(select(Product).where(Product.name == name))
        return result.scalar_one_or_none()

    async def get_by_sku(self, sku: str) -> Product | None:
        result = await self.db.execute(select(Product).where(Product.sku == sku))
        return result.scalar_one_or_none()

    async def name_exists(self, name: str, exclude_id: UUID = None) -> bool:
        inner = select(Product.id).where(Product.name == name)
        if exclude_id:
            inner = inner.where(Product.id != exclude_id)
        result = await self.db.execute(select(inner.exists()))
        return result.scalar()

    async def sku_exists(self, sku: str, exclude_id: UUID = None) -> bool:
        inner = select(Product.id).where(Product.sku == sku)
        if exclude_id:
            inner = inner.where(Product.id != exclude_id)
        result = await self.db.execute(select(inner.exists()))
        return result.scalar()

    async def get_by_category(self, category_id: UUID) -> list[Product]:
        query = (
            select(Product)
            .where(Product.category_id == category_id, Product.is_active == True)
            .order_by(Product.display_order)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_brand(self, brand_id: UUID) -> list[Product]:
        query = (
            select(Product)
            .where(Product.brand_id == brand_id, Product.is_active == True)
            .order_by(Product.display_order)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_featured(self) -> list[Product]:
        query = (
            select(Product)
            .where(Product.is_featured == True, Product.is_active == True)
            .order_by(Product.display_order)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_on_sale(self) -> list[Product]:
        query = (
            select(Product)
            .where(Product.is_discount == True, Product.is_active == True)
            .order_by(Product.display_order)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_low_stock(self) -> list[Product]:
        query = select(Product).where(
            Product.stock_quantity < Product.low_stock_threshold,
            Product.is_active == True,
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def increment_visit_count(self, product_id: UUID) -> None:
        product = await self.get_by_id(product_id)
        if product:
            product.visit_count += 1
            self.db.add(product)
            await self.db.commit()

    async def create(self, product_data: dict) -> Product:
        product = Product(**product_data)
        self.db.add(product)
        await self.db.commit()
        await self.db.refresh(product)
        return product

    async def update(self, product_id: UUID, product_data: dict) -> Product | None:
        product = await self.get_by_id(product_id)
        if not product:
            return None

        for key, value in product_data.items():
            if value is not None and hasattr(product, key):
                setattr(product, key, value)

        self.db.add(product)
        await self.db.commit()
        await self.db.refresh(product)
        return product

    async def delete(self, product_id: UUID, deleted_by: UUID) -> Product | None:
        product = await self.get_by_id(product_id)
        if not product:
            return None

        product.deleted_at = datetime.now(timezone.utc)
        product.deleted_by = deleted_by

        self.db.add(product)
        await self.db.commit()
        await self.db.refresh(product)
        return product

    async def get_all(self, skip: int = 0, limit: int = 10) -> list[Product]:
        query = select(Product).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def count(self) -> int:
        query = select(func.count(Product.id))
        result = await self.db.execute(query)
        return result.scalar_one()
