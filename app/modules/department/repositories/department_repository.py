from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.modules.department.models.department import Department, DepartmentSharepointLink 
from app.modules.department.schemas.response.department_response  import DepartmentResponse


class DepartmentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, department_id: UUID) -> Department | None:
        result = await self.db.execute(
            select(Department)
            .options(selectinload(Department.sharepoint_links))
            .where(Department.id == department_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Department | None:
        result = await self.db.execute(
            select(Department)
            .options(selectinload(Department.sharepoint_links))
            .where(func.lower(Department.name) == name.lower())
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Department | None:
        result = await self.db.execute(
            select(Department)
            .options(selectinload(Department.sharepoint_links))
            .where(func.lower(Department.slug) == slug.lower())
        )
        return result.scalar_one_or_none()

    async def name_exists(self, name: str, exclude_id: UUID | None = None) -> bool:
        inner = select(Department.id).where(func.lower(Department.name) == name.lower())
        if exclude_id:
            inner = inner.where(Department.id != exclude_id)
        result = await self.db.execute(select(inner.exists()))
        return bool(result.scalar())

    async def slug_exists(self, slug: str, exclude_id: UUID | None = None) -> bool:
        inner = select(Department.id).where(func.lower(Department.slug) == slug.lower())
        if exclude_id:
            inner = inner.where(Department.id != exclude_id)
        result = await self.db.execute(select(inner.exists()))
        return bool(result.scalar())

    async def create(self, department: Department) -> Department:
        self.db.add(department)
        await self.db.commit()
        await self.db.refresh(department)
        return department

    async def update(self, department: Department) -> Department:
        self.db.add(department)
        await self.db.commit()
        await self.db.refresh(department)
        return department

    async def delete(self, department: Department, deleted_by: UUID | None = None) -> Department:
        now = datetime.now(timezone.utc)
        department.deleted_at = now
        department.deleted_by = deleted_by

        for link in department.sharepoint_links:
            link.deleted_at = now
            link.deleted_by = deleted_by
            link.sync_enabled = False

        self.db.add(department)
        await self.db.commit()
        await self.db.refresh(department)
        return department

    async def get_link_by_department_and_url_including_deleted(
        self,
        department_id: UUID,
        sharepoint_url: str,
    ) -> DepartmentSharepointLink | None:
        result = await self.db.execute(
            select(DepartmentSharepointLink)
            .where(DepartmentSharepointLink.department_id == department_id)
            .where(DepartmentSharepointLink.sharepoint_url == sharepoint_url),
            execution_options={"include_deleted": True},
        )
        return result.scalar_one_or_none()

    async def list_active_departments(self) -> list[DepartmentResponse]:
        result = await self.db.execute(
            select(
                Department.id.label("id"),
                Department.name.label("name"),
                Department.slug.label("slug"),
                Department.is_active.label("is_active")
            )
            .where(Department.deleted_at.is_(None))
            .where(Department.is_active.is_(True))
        )
        return result.fetchall()