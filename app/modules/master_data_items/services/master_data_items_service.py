"""Master Data Items Service - Business logic layer for master_data_items operations"""
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.master_data_items.models.master_data_items import MasterDataItem
from app.modules.master_data_items.repositories.master_data_items_repository import MasterDataItemRepository
from app.modules.master_data_items.schemas.requests.master_data_items_request import (
    MasterDataItemCreateRequest,
    MasterDataItemUpdateRequest,
)
from app.modules.master_data_items.schemas.response.master_data_items_response import (
    MasterDataItemCollectionResponse,
    MasterDataItemResponse,
    MasterDataItemDetailResponse,
)
from app.schemas.pagination_response import PaginatedCollectionResponse
from app.schemas.request import ListRequestFilters
from app.utils.models.mixin.pagination_query_handler import PaginationQueryHandler


class MasterDataItemService:
    """Handles business logic for master_data_items operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = MasterDataItemRepository(db)
        self.query_handler = PaginationQueryHandler(self.db)

    async def create_master_data_item(self, request: MasterDataItemCreateRequest) -> MasterDataItemResponse:
        """
        Create a new master data item.
        Validates unique code before insertion.
        """
        # Validate unique code first (human-facing, so give a clear error)
        if await self.repo.code_exists(request.code):
            raise ValueError(f"Master data item code '{request.code}' already exists")
        
        if not await self.repo.master_data_id_exists(request.master_data_id):
            raise ValueError(f"Master data ID '{request.master_data_id}' does not exist")

        master_data_item_data = request.model_dump()
        # TODO: Set created_by, updated_by from auth context when implemented

        try:
            created_master_data_item = await self.repo.create(master_data_item_data)
            return MasterDataItemResponse.model_validate(created_master_data_item)
        except IntegrityError as exc:
            await self.db.rollback()
            raise ValueError(
                "Failed to create master data item. Please check your input and try again."
            ) from exc

    async def get_master_data_item_by_id(self, master_data_item_id: UUID) -> MasterDataItemDetailResponse | None:
        """Get a specific master data item by ID"""
        master_data_item = await self.repo.get_by_id(master_data_item_id)
        if master_data_item:
            return MasterDataItemDetailResponse.model_validate(master_data_item)
        return None
    
    async def get_master_data_item_by_code(self, code: str) -> MasterDataItemResponse | None:
        """Get master data item by code"""
        master_data_item = await self.repo.get_by_code(code)
        if master_data_item:
            return MasterDataItemResponse.model_validate(master_data_item)
        return None
    
    async def get_master_data_items_by_master_data_id(self, master_data_id: UUID) -> list[MasterDataItemResponse]:
        """Get all items for a specific master data"""
        master_data_items = await self.repo.get_by_master_data_id(master_data_id)
        return [MasterDataItemResponse.model_validate(item) for item in master_data_items]
    
    async def update_master_data_item(
        self, 
        master_data_item_id: UUID, 
        request: MasterDataItemUpdateRequest
    ) -> MasterDataItemDetailResponse:
        """
        Update an existing master data item.
        Note: updated_at is set automatically by the ORM's onupdate hook.
        """
        master_data_item = await self.repo.get_by_id(master_data_item_id)
        if not master_data_item:
            raise ValueError(f"Master data item not found with ID: {master_data_item_id}")
        if not await self.repo.master_data_id_exists(request.master_data_id):
            raise ValueError(f"Master data ID '{request.master_data_id}' does not exist")
        # Validate unique code if being changed
        if request.code and request.code != master_data_item.code:
            if await self.repo.code_exists(request.code, exclude_id=master_data_item_id):
                raise ValueError(f"Master data item code '{request.code}' already exists")
        
        master_data_item_data = request.model_dump(exclude_unset=True)
        # TODO: Set updated_by from auth context when implemented
        
        updated_master_data_item = await self.repo.update(master_data_item_id, master_data_item_data)
        return MasterDataItemDetailResponse.model_validate(updated_master_data_item)
    
    async def delete_master_data_item(self, master_data_item_id: UUID) -> MasterDataItemDetailResponse:
        """
        Soft delete a master data item.
        Note: deleted_by will be populated from auth context in future.
        """
        master_data_item = await self.repo.get_by_id(master_data_item_id)
        if not master_data_item:
            raise ValueError(f"Master data item not found with ID: {master_data_item_id}")
        
        # TODO: Pass auth user ID when implemented
        deleted_master_data_item = await self.repo.delete(master_data_item_id, None)
        return MasterDataItemDetailResponse.model_validate(deleted_master_data_item)
    
    async def get_master_data_items_paginated(self, params: ListRequestFilters) -> PaginatedCollectionResponse[MasterDataItemCollectionResponse]:
        """Get paginated list of master data items"""
        statement = select(MasterDataItem)

        result = await self.query_handler.execute_paginated_query(
            query=statement,
            model=MasterDataItem,
            params=params,
            searchable_fields=[MasterDataItem.name, MasterDataItem.code, MasterDataItem.description],
            sortable_fields=["created_at", "updated_at", "name", "code", "is_active"]
        )
        return PaginatedCollectionResponse(
            data=result.data,
            pagination=result.pagination
        )
