"""Master Data Items Controller - HTTP request handling for master_data_items endpoints"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.modules.master_data_items.services.master_data_items_service import MasterDataItemService
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
from app.schemas.response import ApiResponse


master_data_items_router = APIRouter()


@master_data_items_router.post("", response_model=ApiResponse[MasterDataItemResponse], status_code=status.HTTP_201_CREATED)
async def create_master_data_item(
    request: MasterDataItemCreateRequest,
    db: AsyncSession = Depends(get_db),
    # TODO: Add current_user parameter when auth dependency is available
) -> dict:
    """Create a new master data item"""
    try:
        service = MasterDataItemService(db)
        # TODO: Pass current_user when auth is implemented
        master_data_item = await service.create_master_data_item(request)
        return ApiResponse(
            success=True,
            message="Master data item created successfully",
            data=master_data_item
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@master_data_items_router.get("/{master_data_item_id}", response_model=ApiResponse[MasterDataItemDetailResponse])
async def get_master_data_item(
    master_data_item_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get a specific master data item by ID"""
    try:
        service = MasterDataItemService(db)
        master_data_item = await service.get_master_data_item_by_id(master_data_item_id)
        if not master_data_item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Master data item not found")
        
        return ApiResponse(
            success=True,
            message="Master data item retrieved successfully",
            data=master_data_item
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@master_data_items_router.get("", response_model=ApiResponse[MasterDataItemCollectionResponse])
async def list_master_data_items(
    request: ListRequestFilters = Depends(ListRequestFilters),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[MasterDataItemCollectionResponse]:
    """Get paginated list of master data items"""
    try:
        service = MasterDataItemService(db)
     
        result = await service.get_master_data_items_paginated(request)
        
        return ApiResponse(
            success=True,
            message="Master data items retrieved successfully",
            data=MasterDataItemCollectionResponse(
               data=result.data
            ),
            paginations=result.pagination
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@master_data_items_router.put("/{master_data_item_id}", response_model=ApiResponse[MasterDataItemDetailResponse])
async def update_master_data_item(
    master_data_item_id: UUID,
    request: MasterDataItemUpdateRequest,
    db: AsyncSession = Depends(get_db),
    # TODO: Add current_user parameter when auth dependency is available
) -> dict:
    """Update an existing master data item"""
    try:
        service = MasterDataItemService(db)
        # TODO: Pass current_user when auth is implemented
        master_data_item = await service.update_master_data_item(master_data_item_id, request)
        
        return ApiResponse(
            success=True,
            message="Master data item updated successfully",
            data=master_data_item
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@master_data_items_router.delete("/{master_data_item_id}", response_model=ApiResponse[MasterDataItemDetailResponse])
async def delete_master_data_item(
    master_data_item_id: UUID,
    db: AsyncSession = Depends(get_db),
    # TODO: Add current_user parameter when auth dependency is available
) -> dict:
    """Soft delete a master data item"""
    try:
        service = MasterDataItemService(db)
        # TODO: Pass current_user when auth is implemented
        master_data_item = await service.delete_master_data_item(master_data_item_id)
        
        return ApiResponse(
            success=True,
            message="Master data item deleted successfully",
            data=master_data_item
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
