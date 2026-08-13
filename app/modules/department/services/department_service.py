from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.department.models.department import Department, DepartmentSharepointLink
from app.modules.department.repositories.department_repository import DepartmentRepository
from app.modules.department.schemas.requests.department_request import (
    DepartmentCreateRequest,
    DepartmentUpdateRequest,
)
from app.modules.department.schemas.response.department_response import DepartmentResponse
from app.schemas.request import ListRequestFilters
from app.utils.models.mixin.pagination_query_handler import PaginationQueryHandler



class DepartmentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = DepartmentRepository(db)
        self.query_handler = PaginationQueryHandler(db)

    async def create_department(
        self,
        request: DepartmentCreateRequest,
        created_by: UUID | None = None,
    ) -> DepartmentResponse:
        if await self.repo.name_exists(request.name):
            raise ValueError(f"Department name '{request.name}' already exists")
        if await self.repo.slug_exists(request.slug):
            raise ValueError(f"Department slug '{request.slug}' already exists")

        department = Department(
            name=request.name,
            slug=request.slug,
            description=request.description,
            is_active=request.is_active,
            created_by=created_by,
            updated_by=created_by,
            sharepoint_links=[
                DepartmentSharepointLink(
                    sharepoint_url=link.sharepoint_url,
                    label=link.label,
                    sync_enabled=link.sync_enabled,
                    created_by=created_by,
                    updated_by=created_by,
                )
                for link in request.sharepoint_links
            ],
        )

        created = await self.repo.create(department)
        return DepartmentResponse.model_validate(created)

    async def get_department_by_id(self, department_id: UUID) -> DepartmentResponse | None:
        department = await self.repo.get_by_id(department_id)
        if not department:
            return None
        return DepartmentResponse.model_validate(department)

    async def update_department(
        self,
        department_id: UUID,
        request: DepartmentUpdateRequest,
        updated_by: UUID | None = None,
    ) -> DepartmentResponse:
        department = await self.repo.get_by_id(department_id)
        if not department:
            raise ValueError(f"Department not found with ID: {department_id}")

        if request.name and request.name != department.name:
            if await self.repo.name_exists(request.name, exclude_id=department_id):
                raise ValueError(f"Department name '{request.name}' already exists")
            department.name = request.name

        if request.slug and request.slug != department.slug:
            if await self.repo.slug_exists(request.slug, exclude_id=department_id):
                raise ValueError(f"Department slug '{request.slug}' already exists")
            department.slug = request.slug

        if request.description is not None:
            department.description = request.description

        if request.is_active is not None:
            department.is_active = request.is_active

        if request.sharepoint_links is not None:
            now = datetime.now(timezone.utc)
            active_by_url = {
                link.sharepoint_url: link
                for link in department.sharepoint_links
                if link.deleted_at is None
            }
            requested_by_url = {link.sharepoint_url: link for link in request.sharepoint_links}

            for url, existing_link in active_by_url.items():
                if url not in requested_by_url:
                    existing_link.deleted_at = now
                    existing_link.deleted_by = updated_by
                    existing_link.sync_enabled = False

            for url, payload_link in requested_by_url.items():
                existing_link = active_by_url.get(url)
                if existing_link:
                    existing_link.label = payload_link.label
                    existing_link.sync_enabled = payload_link.sync_enabled
                    existing_link.updated_by = updated_by
                    continue

                reusable_link = await self.repo.get_link_by_department_and_url_including_deleted(
                    department_id=department.id,
                    sharepoint_url=url,
                )
                if reusable_link:
                    reusable_link.deleted_at = None
                    reusable_link.deleted_by = None
                    reusable_link.label = payload_link.label
                    reusable_link.sync_enabled = payload_link.sync_enabled
                    reusable_link.updated_by = updated_by
                else:
                    department.sharepoint_links.append(
                        DepartmentSharepointLink(
                            department_id=department.id,
                            sharepoint_url=payload_link.sharepoint_url,
                            label=payload_link.label,
                            sync_enabled=payload_link.sync_enabled,
                            created_by=updated_by,
                            updated_by=updated_by,
                        )
                    )

        department.updated_by = updated_by
        updated = await self.repo.update(department)
        return DepartmentResponse.model_validate(updated)

    async def delete_department(
        self,
        department_id: UUID,
        deleted_by: UUID | None = None,
    ) -> DepartmentResponse:
        department = await self.repo.get_by_id(department_id)
        if not department:
            raise ValueError(f"Department not found with ID: {department_id}")

        deleted = await self.repo.delete(department=department, deleted_by=deleted_by)
        return DepartmentResponse.model_validate(deleted)

    async def get_departments_paginated(self, params: ListRequestFilters) -> dict:
        result = await self.query_handler.execute_paginated_query(
            query=select(Department),
            model=Department,
            params=params,
            searchable_fields=[Department.name, Department.slug, Department.description],
            sortable_fields=["created_at", "updated_at", "name", "slug"],
        )

        departments = [DepartmentResponse.model_validate(item) for item in result.data]
        return {"data": departments, "pagination": result.pagination}

    async def list_active_departments(self) -> list[DepartmentResponse]:
        departments = await self.repo.list_active_departments()

        return [DepartmentResponse.model_validate(row._mapping) for row in departments]