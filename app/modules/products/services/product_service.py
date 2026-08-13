from types import SimpleNamespace
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.modules.products.repositories.product_repository import ProductRepository
from app.modules.products.schemas.requests.product_request import ProductCreateRequest, ProductUpdateRequest
from app.utils.models.mixin.pagination_query_handler import PaginationQueryHandler
from app.modules.products.models.product import Product


class ProductService:
    """Service for product business logic."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ProductRepository(db)
        self.query_handler = PaginationQueryHandler(db)

    async def create_product(self, product_request: ProductCreateRequest, created_by: UUID) -> Product:
        if await self.repo.name_exists(product_request.name):
            raise ValueError(f"Product with name '{product_request.name}' already exists")

        if await self.repo.sku_exists(product_request.sku):
            raise ValueError(f"Product with SKU '{product_request.sku}' already exists")

        product_data = product_request.model_dump()
        product_data["created_by"] = created_by
        product_data["updated_by"] = created_by

        return await self.repo.create(product_data)

    async def get_product_by_id(self, product_id: UUID) -> Product | None:
        product = await self.repo.get_by_id(product_id)
        if product:
            await self.repo.increment_visit_count(product_id)
        return product

    async def get_product_by_name(self, name: str) -> Product | None:
        return await self.repo.get_by_name(name)

    async def get_product_by_sku(self, sku: str) -> Product | None:
        return await self.repo.get_by_sku(sku)

    async def get_products_by_category(self, category_id: UUID) -> list[Product]:
        return await self.repo.get_by_category(category_id)

    async def get_products_by_brand(self, brand_id: UUID) -> list[Product]:
        return await self.repo.get_by_brand(brand_id)

    async def get_featured_products(self) -> list[Product]:
        return await self.repo.get_featured()

    async def get_products_on_sale(self) -> list[Product]:
        return await self.repo.get_on_sale()

    async def get_low_stock_products(self) -> list[Product]:
        return await self.repo.get_low_stock()

    async def update_product(self, product_id: UUID, product_request: ProductUpdateRequest, updated_by: UUID) -> Product:
        product = await self.repo.get_by_id(product_id)
        if not product:
            raise ValueError(f"Product with ID '{product_id}' not found")

        if product_request.name and product_request.name != product.name:
            if await self.repo.name_exists(product_request.name, exclude_id=product_id):
                raise ValueError(f"Product with name '{product_request.name}' already exists")

        if product_request.sku and product_request.sku != product.sku:
            if await self.repo.sku_exists(product_request.sku, exclude_id=product_id):
                raise ValueError(f"Product with SKU '{product_request.sku}' already exists")

        product_data = product_request.model_dump(exclude_unset=True)
        product_data["updated_by"] = updated_by

        updated = await self.repo.update(product_id, product_data)
        return updated

    async def delete_product(self, product_id: UUID, deleted_by: UUID) -> Product:
        product = await self.repo.get_by_id(product_id)
        if not product:
            raise ValueError(f"Product with ID '{product_id}' not found")

        return await self.repo.delete(product_id, deleted_by)

    async def get_products_paginated(self, search: str = None, sort: str = None,
                                     page: int = 1, limit: int = 10) -> dict:
        order_by = "updated_at"
        sort_order = "desc"
        if sort:
            if sort.startswith("-"):
                order_by = sort[1:]
                sort_order = "desc"
            else:
                order_by = sort
                sort_order = "asc"

        params = SimpleNamespace(
            skip=max(0, (page - 1) * limit),
            limit=limit,
            search=search,
            order_by=order_by,
            sort_order=sort_order,
        )

        result = await self.query_handler.execute_paginated_query(
            query=select(Product),
            model=Product,
            params=params,
            searchable_fields=[Product.name, Product.title, Product.sku, Product.mpn],
            sortable_fields=["created_at", "updated_at", "name", "price", "display_order"],
        )

        return {"data": result.data, "pagination": result.pagination}
