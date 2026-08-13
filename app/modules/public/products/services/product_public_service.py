from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from decimal import Decimal
from app.modules.products.models.product import Product


class ProductPublicService:
    """Service for public product operations (read-only with advanced filtering)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_featured_products(self) -> list[Product]:
        query = (
            select(Product)
            .where(Product.is_featured == True, Product.is_active == True)
            .order_by(Product.display_order)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_on_sale_products(self) -> list[Product]:
        query = (
            select(Product)
            .where(Product.is_discount == True, Product.is_active == True)
            .order_by(Product.display_order)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_products_by_category(self, category_id: UUID) -> list[Product]:
        query = (
            select(Product)
            .where(Product.category_id == category_id, Product.is_active == True)
            .order_by(Product.display_order)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_products_by_brand(self, brand_id: UUID) -> list[Product]:
        query = (
            select(Product)
            .where(Product.brand_id == brand_id, Product.is_active == True)
            .order_by(Product.display_order)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def search_products(
        self,
        search: str = None,
        category_id: UUID = None,
        brand_id: UUID = None,
        min_price: Decimal = None,
        max_price: Decimal = None,
        in_stock_only: bool = False,
    ) -> list[Product]:
        query = select(Product).where(Product.is_active == True)

        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Product.title.ilike(search_term),
                    Product.name.ilike(search_term),
                    Product.sku.ilike(search_term),
                )
            )

        if category_id:
            query = query.where(Product.category_id == category_id)

        if brand_id:
            query = query.where(Product.brand_id == brand_id)

        if min_price is not None:
            query = query.where(Product.price >= min_price)

        if max_price is not None:
            query = query.where(Product.price <= max_price)

        if in_stock_only:
            query = query.where(Product.stock_quantity > 0)

        query = query.order_by(Product.display_order)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_product_by_id(self, product_id: UUID) -> Product | None:
        query = select(Product).where(Product.id == product_id, Product.is_active == True)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_product_by_name(self, name: str) -> Product | None:
        query = select(Product).where(Product.name == name, Product.is_active == True)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def increment_visit_count(self, product_id: UUID) -> None:
        product = await self.get_product_by_id(product_id)
        if product:
            product.visit_count += 1
            self.db.add(product)
            await self.db.commit()
