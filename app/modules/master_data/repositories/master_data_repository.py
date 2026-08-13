"""Master Data Repository - Data access layer for master_data operations"""
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime, timezone
from app.modules.master_data.models.master_data import MasterData


class MasterDataRepository:
    """Repository for master_data database operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, master_data_id: UUID) -> MasterData | None:
        """Get master data by ID"""
        result = await self.db.execute(select(MasterData).where(MasterData.id == master_data_id))
        return result.scalar_one_or_none()
    
    async def get_by_name(self, name: str) -> MasterData | None:
        """Get master data by unique name"""
        result = await self.db.execute(select(MasterData).where(MasterData.name == name))
        return result.scalar_one_or_none()
    
    async def name_exists(self, name: str, exclude_id: UUID = None) -> bool:
        """
        Check if a master data name already exists.
        Uses SELECT EXISTS(...) so PostgreSQL short-circuits on the first match.
        """
        inner = select(MasterData.id).where(func.lower(MasterData.name) == name.lower())
        if exclude_id:
            inner = inner.where(MasterData.id != exclude_id)
        result = await self.db.execute(select(inner.exists()))
        return result.scalar()

    async def get_all_active(self, limit: int = 1000) -> list[MasterData]:
        """Get active master data entries (capped at `limit` rows to prevent OOM)."""
        query = select(MasterData).where(MasterData.is_active == True).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_all_paginated(self, skip: int = 0, limit: int = 10) -> list[MasterData]:
        """Get master data with pagination"""
        query = select(MasterData).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_total_count(self) -> int:
        """Get total count of active master data entries"""
        query = select(func.count(MasterData.id)).where(MasterData.is_active == True)
        result = await self.db.execute(query)
        return result.scalar_one()

    async def create(self, master_data_data: dict) -> MasterData:
        """Create a new master data entry"""
        master_data = MasterData(**master_data_data)
        self.db.add(master_data)
        await self.db.commit()
        await self.db.refresh(master_data)
        return master_data
    
    async def update(self, master_data_id: UUID, master_data_data: dict) -> MasterData | None:
        """Update an existing master data entry"""
        master_data = await self.get_by_id(master_data_id)
        if not master_data:
            return None
        
        for key, value in master_data_data.items():
            if value is not None and hasattr(master_data, key):
                setattr(master_data, key, value)
        
        self.db.add(master_data)
        await self.db.commit()
        await self.db.refresh(master_data)
        return master_data
    
    async def delete(self, master_data_id: UUID, deleted_by: UUID) -> MasterData | None:
        """Soft delete a master data entry"""
        master_data = await self.get_by_id(master_data_id)
        if not master_data:
            return None
        
        master_data.deleted_at = datetime.now(timezone.utc)
        master_data.deleted_by = deleted_by
        
        self.db.add(master_data)
        await self.db.commit()
        await self.db.refresh(master_data)
        return master_data
    
    async def get_by_id_soft_deleted(self, master_data_id: UUID) -> MasterData | None:
        """Fetch a master data entry that has been soft-deleted (bypasses the global filter)."""
        query = (
            select(MasterData)
            .where(MasterData.id == master_data_id)
            .where(MasterData.deleted_at.isnot(None))
        )
        
        result = await self.db.execute(
            query,
            execution_options={"include_deleted": True}
        )
        return result.scalar_one_or_none()
