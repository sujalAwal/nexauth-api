"""Tenant Repository - Data access layer for tenant operations"""
from sqlalchemy import func, select, exists as sa_exists
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime, timezone
from app.modules.tenant.models.tenant import Tenant


class TenantRepository:
    """Repository for tenant database operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, tenant_id: UUID) -> Tenant | None:
        """Get tenant by ID"""
        result = await self.db.execute(select(Tenant).where(Tenant.id == tenant_id))
        return result.scalar_one_or_none()
    
    
    async def get_by_name(self, name: str) -> Tenant | None:
        """Get tenant by unique name"""
        result = await self.db.execute(select(Tenant).where(Tenant.name == name))
        return result.scalar_one_or_none()
    
    async def get_by_code(self, code: int) -> Tenant | None:
        """Get tenant by unique code"""
        result = await self.db.execute(select(Tenant).where(Tenant.code == code))
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Tenant | None:
        """Get tenant by unique slug (case-insensitive)"""
        result = await self.db.execute(
            select(Tenant).where(func.lower(Tenant.slug) == slug.lower())
        )
        return result.scalar_one_or_none()
    
    async def name_exists(self, name: str, exclude_id: UUID = None) -> bool:
        """
        Check if a tenant name already exists.
        Uses SELECT EXISTS(...) so PostgreSQL short-circuits on the first match
        — no need to fetch and return the column value.
        """
        inner = select(Tenant.id).where(func.lower(Tenant.name) == name.lower())
        if exclude_id:
            inner = inner.where(Tenant.id != exclude_id)
        result = await self.db.execute(select(inner.exists()))
        return result.scalar()

    async def slug_exists(self, slug: str, exclude_id: UUID = None) -> bool:
        """
        Check if a tenant slug already exists (case-insensitive).
        Uses SELECT EXISTS(...) for short-circuit evaluation.
        """
        inner = select(Tenant.id).where(func.lower(Tenant.slug) == slug.lower())
        if exclude_id:
            inner = inner.where(Tenant.id != exclude_id)
        result = await self.db.execute(select(inner.exists()))
        return bool(result.scalar())
    
    async def code_exists(self, code: int, exclude_id: UUID = None) -> bool:
        """
        Check if a tenant code already exists.
        Uses SELECT EXISTS(...) for the same short-circuit benefit.
        """
        inner = select(Tenant.id).where(Tenant.code == code)
        if exclude_id:
            inner = inner.where(Tenant.id != exclude_id)
        result = await self.db.execute(select(inner.exists()))
        return result.scalar()

    async def get_all_active(self, limit: int = 1000) -> list[Tenant]:
        """Get active tenants (capped at `limit` rows to prevent OOM on large datasets)."""
        query = select(Tenant).where(Tenant.is_active == True).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_all_paginated(self, skip: int = 0, limit: int = 10) -> list[Tenant]:
        """Get tenants with pagination"""
        query = select(Tenant).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_total_count(self) -> int:
        """Get total count of active tenants"""
        query = select(func.count(Tenant.id)).where(Tenant.is_active == True)
        result = await self.db.execute(query)
        return result.scalar_one()

    async def create(self, tenant_data: dict) -> Tenant:
        """Create a new tenant"""
        tenant = Tenant(**tenant_data)
        self.db.add(tenant)
        await self.db.commit()
        await self.db.refresh(tenant)
        return tenant
    
    async def update(self, tenant_id: UUID, tenant_data: dict) -> Tenant | None:
        """Update an existing tenant"""
        tenant = await self.get_by_id(tenant_id)
        if not tenant:
            return None
        
        for key, value in tenant_data.items():
            if value is not None and hasattr(tenant, key):
                setattr(tenant, key, value)
        
        self.db.add(tenant)
        await self.db.commit()
        await self.db.refresh(tenant)
        return tenant
    
    async def delete(self, tenant_id: UUID, deleted_by: UUID) -> Tenant | None:
        """Soft delete a tenant"""
        tenant = await self.get_by_id(tenant_id)
        if not tenant:
            return None
        
        tenant.deleted_at = datetime.now(timezone.utc)
        tenant.deleted_by = deleted_by
        
        self.db.add(tenant)
        await self.db.commit()
        await self.db.refresh(tenant)
        return tenant
    
    async def restore(self, tenant_id: UUID) -> Tenant | None:
        """Restore a soft-deleted tenant"""
        tenant = await self.get_by_id_soft_deleted(tenant_id)
        if not tenant:
            return None

        tenant.deleted_at = None
        tenant.deleted_by = None
        
        self.db.add(tenant)       # was missing — explicit dirty-tracking consistent with other methods
        await self.db.commit()
        await self.db.refresh(tenant)
        return tenant
    
    
    async def get_by_id_soft_deleted(self, tenant_id: UUID) -> Tenant | None:
        """Fetch a tenant that has been soft-deleted (bypasses the global filter)."""
        query = (
            select(Tenant)
            .where(Tenant.id == tenant_id)
            .where(Tenant.deleted_at.isnot(None))
        )
        
        result = await self.db.execute(
            query,
            execution_options={"include_deleted": True}
        )
        return result.scalar_one_or_none()