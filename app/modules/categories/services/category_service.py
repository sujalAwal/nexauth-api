from types import SimpleNamespace
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.modules.categories.repositories.category_repository import CategoryRepository
from app.modules.categories.schemas.requests.category_request import CategoryCreateRequest, CategoryUpdateRequest
from app.utils.models.mixin.pagination_query_handler import PaginationQueryHandler
from app.modules.categories.models.category import Category


class CategoryService:
    """Service for category business logic."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = CategoryRepository(db)
        self.query_handler = PaginationQueryHandler(db)

    async def create_category(self, category_request: CategoryCreateRequest, created_by: UUID) -> Category:
        if await self.repo.name_exists(category_request.name):
            raise ValueError(f"Category with name '{category_request.name}' already exists")

        category_data = category_request.model_dump()
        category_data["created_by"] = created_by
        category_data["updated_by"] = created_by

        return await self.repo.create(category_data)

    async def get_category_by_id(self, category_id: UUID) -> Category | None:
        return await self.repo.get_by_id(category_id)

    async def get_category_by_name(self, name: str) -> Category | None:
        return await self.repo.get_by_name(name)

    async def get_featured_categories(self) -> list[Category]:
        return await self.repo.get_featured()

    async def update_category(self, category_id: UUID, category_request: CategoryUpdateRequest, updated_by: UUID) -> Category:
        category = await self.repo.get_by_id(category_id)
        if not category:
            raise ValueError(f"Category with ID '{category_id}' not found")

        if category_request.name and category_request.name != category.name:
            if await self.repo.name_exists(category_request.name, exclude_id=category_id):
                raise ValueError(f"Category with name '{category_request.name}' already exists")

        category_data = category_request.model_dump(exclude_unset=True)
        category_data["updated_by"] = updated_by

        updated = await self.repo.update(category_id, category_data)
        return updated

    async def delete_category(self, category_id: UUID, deleted_by: UUID) -> Category:
        category = await self.repo.get_by_id(category_id)
        if not category:
            raise ValueError(f"Category with ID '{category_id}' not found")

        return await self.repo.delete(category_id, deleted_by)

    async def get_categories_paginated(self, search: str = None, sort: str = None,
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
            query=select(Category),
            model=Category,
            params=params,
            searchable_fields=[Category.name, Category.title, Category.description],
            sortable_fields=["created_at", "updated_at", "name", "display_order"],
        )

        return {"data": result.data, "pagination": result.pagination}
