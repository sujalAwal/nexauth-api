from types import SimpleNamespace
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.modules.brands.repositories.brand_repository import BrandRepository
from app.modules.brands.schemas.requests.brand_request import BrandCreateRequest, BrandUpdateRequest
from app.utils.models.mixin.pagination_query_handler import PaginationQueryHandler
from app.modules.brands.models.brand import Brand


class BrandService:
    """Service for brand business logic."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = BrandRepository(db)
        self.query_handler = PaginationQueryHandler(db)

    async def create_brand(self, brand_request: BrandCreateRequest, created_by: UUID) -> Brand:
        if await self.repo.name_exists(brand_request.name):
            raise ValueError(f"Brand with name '{brand_request.name}' already exists")

        brand_data = brand_request.model_dump()
        brand_data["created_by"] = created_by
        brand_data["updated_by"] = created_by

        return await self.repo.create(brand_data)

    async def get_brand_by_id(self, brand_id: UUID) -> Brand | None:
        return await self.repo.get_by_id(brand_id)

    async def get_brand_by_name(self, name: str) -> Brand | None:
        return await self.repo.get_by_name(name)

    async def get_featured_brands(self) -> list[Brand]:
        return await self.repo.get_featured()

    async def update_brand(self, brand_id: UUID, brand_request: BrandUpdateRequest, updated_by: UUID) -> Brand:
        brand = await self.repo.get_by_id(brand_id)
        if not brand:
            raise ValueError(f"Brand with ID '{brand_id}' not found")

        if brand_request.name and brand_request.name != brand.name:
            if await self.repo.name_exists(brand_request.name, exclude_id=brand_id):
                raise ValueError(f"Brand with name '{brand_request.name}' already exists")

        brand_data = brand_request.model_dump(exclude_unset=True)
        brand_data["updated_by"] = updated_by

        updated = await self.repo.update(brand_id, brand_data)
        return updated

    async def delete_brand(self, brand_id: UUID, deleted_by: UUID) -> Brand:
        brand = await self.repo.get_by_id(brand_id)
        if not brand:
            raise ValueError(f"Brand with ID '{brand_id}' not found")

        return await self.repo.delete(brand_id, deleted_by)

    async def increment_visit_count(self, brand_id: UUID) -> None:
        brand = await self.repo.get_by_id(brand_id)
        if not brand:
            raise ValueError(f"Brand with ID '{brand_id}' not found")

        await self.repo.increment_visit_count(brand_id)

    async def get_brands_paginated(self, search: str = None, sort: str = None,
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
            query=select(Brand),
            model=Brand,
            params=params,
            searchable_fields=[Brand.name, Brand.title, Brand.country_of_origin],
            sortable_fields=["created_at", "updated_at", "name", "title"],
        )

        return {"data": result.data, "pagination": result.pagination}
