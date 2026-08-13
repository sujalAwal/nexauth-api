"""Master Data Items Repository - Data access layer for master_data_items operations"""
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime, timezone
from app.modules.master_data_items.models.master_data_items import MasterDataItem


class MasterDataItemRepository:
    """Repository for master_data_items database operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, master_data_item_id: UUID) -> MasterDataItem | None:
        """Get master data item by ID"""
        result = await self.db.execute(select(MasterDataItem).where(MasterDataItem.id == master_data_item_id))
        return result.scalar_one_or_none()
    
    async def get_by_code(self, code: str) -> MasterDataItem | None:
        """Get master data item by unique code"""
        result = await self.db.execute(select(MasterDataItem).where(MasterDataItem.code == code))
        return result.scalar_one_or_none()
    
    async def get_by_master_data_id(self, master_data_id: UUID, limit: int = 1000) -> list[MasterDataItem]:
        """Get all items for a specific master data"""
        query = select(MasterDataItem).where(MasterDataItem.master_data_id == master_data_id).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def code_exists(self, code: str, exclude_id: UUID = None) -> bool:
        """
        Check if a master data item code already exists.
        Uses SELECT EXISTS(...) so PostgreSQL short-circuits on the first match.
        """
        inner = select(MasterDataItem.id).where(MasterDataItem.code == code)
        if exclude_id:
            inner = inner.where(MasterDataItem.id != exclude_id)
        result = await self.db.execute(select(inner.exists()))
        return result.scalar()

    async def get_all_active(self, limit: int = 1000) -> list[MasterDataItem]:
        """Get active master data items (capped at `limit` rows to prevent OOM)."""
        query = select(MasterDataItem).where(MasterDataItem.is_active == True).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_all_paginated(self, skip: int = 0, limit: int = 10) -> list[MasterDataItem]:
        """Get master data items with pagination"""
        query = select(MasterDataItem).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_total_count(self) -> int:
        """Get total count of active master data items"""
        query = select(func.count(MasterDataItem.id)).where(MasterDataItem.is_active == True)
        result = await self.db.execute(query)
        return result.scalar_one()

    async def create(self, master_data_item_data: dict) -> MasterDataItem:
        """Create a new master data item"""
        master_data_item = MasterDataItem(**master_data_item_data)
        self.db.add(master_data_item)
        await self.db.commit()
        await self.db.refresh(master_data_item)
        return master_data_item
    
    async def update(self, master_data_item_id: UUID, master_data_item_data: dict) -> MasterDataItem | None:
        """Update an existing master data item"""
        master_data_item = await self.get_by_id(master_data_item_id)
        if not master_data_item:
            return None
        
        for key, value in master_data_item_data.items():
            if value is not None and hasattr(master_data_item, key):
                setattr(master_data_item, key, value)
        
        self.db.add(master_data_item)
        await self.db.commit()
        await self.db.refresh(master_data_item)
        return master_data_item
    
    async def delete(self, master_data_item_id: UUID, deleted_by: UUID) -> MasterDataItem | None:
        """Soft delete a master data item"""
        master_data_item = await self.get_by_id(master_data_item_id)
        if not master_data_item:
            return None
        
        master_data_item.deleted_at = datetime.now(timezone.utc)
        master_data_item.deleted_by = deleted_by
        
        self.db.add(master_data_item)
        await self.db.commit()
        await self.db.refresh(master_data_item)
        return master_data_item
    
    async def get_by_id_soft_deleted(self, master_data_item_id: UUID) -> MasterDataItem | None:
        """Fetch a master data item that has been soft-deleted (bypasses the global filter)."""
        query = (
            select(MasterDataItem)
            .where(MasterDataItem.id == master_data_item_id)
            .where(MasterDataItem.deleted_at.isnot(None))
        )
        
        result = await self.db.execute(
            query,
            execution_options={"include_deleted": True}
        )
        return result.scalar_one_or_none()
    
    async def master_data_id_exists(self, master_data_id: UUID) -> bool:

        inner = select(MasterDataItem.id).where(MasterDataItem.master_data_id == master_data_id)
        result = await self.db.execute(select(inner.exists()))
        return result.scalar()
