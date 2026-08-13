"""Master Data Service - Business logic layer for master_data operations"""
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.master_data.models.master_data import MasterData
from app.modules.master_data.repositories.master_data_repository import MasterDataRepository
from app.modules.master_data.schemas.requests.master_data_request import (
    MasterDataCreateRequest,
    MasterDataUpdateRequest,
)
from app.modules.master_data.schemas.response.master_data_response import (
    MasterDataCollectionResponse,
    MasterDataResponse,
    MasterDataDetailResponse,
)
from app.schemas.pagination_response import PaginatedCollectionResponse
from app.schemas.request import ListRequestFilters
from app.utils.models.mixin.pagination_query_handler import PaginationQueryHandler


class MasterDataService:
    """Handles business logic for master_data operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = MasterDataRepository(db)
        self.query_handler = PaginationQueryHandler(self.db)

    async def create_master_data(self, request: MasterDataCreateRequest) -> MasterDataResponse:
        """
        Create a new master data entry.
        Validates unique name before insertion.
        """
        # Validate unique name first (human-facing, so give a clear error)
        if await self.repo.name_exists(request.name):
            raise ValueError(f"Master data name '{request.name}' already exists")

        master_data_data = request.model_dump()
        # TODO: Set created_by, updated_by from auth context when implemented

        try:
            created_master_data = await self.repo.create(master_data_data)
            return MasterDataResponse.model_validate(created_master_data)
        except IntegrityError as exc:
            await self.db.rollback()
            raise ValueError(
                "Failed to create master data. Please check your input and try again."
            ) from exc

    async def get_master_data_by_id(self, master_data_id: UUID) -> MasterDataDetailResponse | None:
        """Get a specific master data entry by ID"""
        master_data = await self.repo.get_by_id(master_data_id)
        if master_data:
            return MasterDataDetailResponse.model_validate(master_data)
        return None
    
    async def get_master_data_by_name(self, name: str) -> MasterDataResponse | None:
        """Get master data by name"""
        master_data = await self.repo.get_by_name(name)
        if master_data:
            return MasterDataResponse.model_validate(master_data)
        return None
    
    async def update_master_data(
        self, 
        master_data_id: UUID, 
        request: MasterDataUpdateRequest
    ) -> MasterDataDetailResponse:
        """
        Update an existing master data entry.
        Note: updated_at is set automatically by the ORM's onupdate hook.
        """
        master_data = await self.repo.get_by_id(master_data_id)
        if not master_data:
            raise ValueError(f"Master data not found with ID: {master_data_id}")
        
        # Validate unique name if being changed
        if request.name and request.name != master_data.name:
            if await self.repo.name_exists(request.name, exclude_id=master_data_id):
                raise ValueError(f"Master data name '{request.name}' already exists")
        
        master_data_data = request.model_dump(exclude_unset=True)
        # TODO: Set updated_by from auth context when implemented
        
        updated_master_data = await self.repo.update(master_data_id, master_data_data)
        return MasterDataDetailResponse.model_validate(updated_master_data)
    
    async def delete_master_data(self, master_data_id: UUID) -> MasterDataDetailResponse:
        """
        Soft delete a master data entry.
        Note: deleted_by will be populated from auth context in future.
        """
        master_data = await self.repo.get_by_id(master_data_id)
        if not master_data:
            raise ValueError(f"Master data not found with ID: {master_data_id}")
        
        # TODO: Pass auth user ID when implemented
        deleted_master_data = await self.repo.delete(master_data_id, None)
        return MasterDataDetailResponse.model_validate(deleted_master_data)
    
    async def get_master_data_paginated(self, params: ListRequestFilters) -> PaginatedCollectionResponse[MasterDataCollectionResponse]:
        """Get paginated list of master data entries"""
        try:
            statement = select(MasterData)

            result = await self.query_handler.execute_paginated_query(
                query=statement,
                model=MasterData,
                params=params,
                searchable_fields=[MasterData.name, MasterData.description],
                sortable_fields=["created_at", "updated_at", "name", "is_active"]
            )
            return PaginatedCollectionResponse(
                data=result.data,
                pagination=result.pagination
            )
        except Exception as e:
            raise Exception(f"Failed to retrieve master data: {str(e)}") from e
