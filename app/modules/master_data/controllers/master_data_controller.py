
"""Master Data Controller - HTTP request handling for master_data endpoints"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.modules.master_data.services.master_data_service import MasterDataService
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
from app.schemas.response import ApiResponse


master_data_router = APIRouter()


@master_data_router.post("", response_model=ApiResponse[MasterDataResponse], status_code=status.HTTP_201_CREATED)
async def create_master_data(
    request: MasterDataCreateRequest,
    db: AsyncSession = Depends(get_db),
    # TODO: Add current_user parameter when auth dependency is available
) -> dict:
    """Create a new master data entry"""
    try:
        service = MasterDataService(db)
        # TODO: Pass current_user when auth is implemented
        master_data = await service.create_master_data(request)
        return ApiResponse(
            success=True,
            message="Master data created successfully",
            data=master_data
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@master_data_router.get("/{master_data_id}", response_model=ApiResponse[MasterDataDetailResponse])
async def get_master_data(
    master_data_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get a specific master data entry by ID"""
    try:
        service = MasterDataService(db)
        master_data = await service.get_master_data_by_id(master_data_id)
        if not master_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Master data not found")
        
        return ApiResponse(
            success=True,
            message="Master data retrieved successfully",
            data=master_data
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@master_data_router.get("", response_model=ApiResponse[MasterDataCollectionResponse])
async def list_master_data(
    request: ListRequestFilters = Depends(ListRequestFilters),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[MasterDataCollectionResponse]:
    """Get paginated list of master data entries"""
    try:
        service = MasterDataService(db)
     
        result = await service.get_master_data_paginated(request)
        
        return ApiResponse(
            success=True,
            message="Master data retrieved successfully",
            data=MasterDataCollectionResponse(
               data=result.data
            ),
            paginations=result.pagination
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@master_data_router.put("/{master_data_id}", response_model=ApiResponse[MasterDataDetailResponse])
async def update_master_data(
    master_data_id: UUID,
    request: MasterDataUpdateRequest,
    db: AsyncSession = Depends(get_db),
    # TODO: Add current_user parameter when auth dependency is available
) -> dict:
    """Update an existing master data entry"""
    try:
        service = MasterDataService(db)
        # TODO: Pass current_user when auth is implemented
        master_data = await service.update_master_data(master_data_id, request)
        
        return ApiResponse(
            success=True,
            message="Master data updated successfully",
            data=master_data
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@master_data_router.delete("/{master_data_id}", response_model=ApiResponse[MasterDataDetailResponse])
async def delete_master_data(
    master_data_id: UUID,
    db: AsyncSession = Depends(get_db),
    # TODO: Add current_user parameter when auth dependency is available
) -> dict:
    """Soft delete a master data entry"""
    try:
        service = MasterDataService(db)
        # TODO: Pass current_user when auth is implemented
        master_data = await service.delete_master_data(master_data_id)
        
        return ApiResponse(
            success=True,
            message="Master data deleted successfully",
            data=master_data
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))