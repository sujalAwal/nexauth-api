"""Tenant Controller - HTTP request handling for tenant endpoints"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.modules.tenant.services.tenant_service import TenantService
from app.modules.tenant.schemas.requests.tenant_request import (
    TenantCreateRequest,
    TenantUpdateRequest,
)
from app.modules.tenant.schemas.response.tenant_response import (
    TenantCollectionResponse,
    TenantResponse,
    TenantDetailResponse,
)
from app.schemas import request
from app.schemas.pagination_response import PaginatedCollectionResponse
from app.schemas.request import ListRequestFilters
from app.schemas.response import ApiResponse 
# TODO: Import authentication dependency when auth module is implemented


tenant_router   = APIRouter()


@tenant_router.post("", response_model=ApiResponse[TenantResponse], status_code=status.HTTP_201_CREATED)
async def create_tenant(
    request: TenantCreateRequest,
    db: AsyncSession = Depends(get_db),
    # TODO: Add current_user parameter when auth dependency is available
) -> dict:
    """Create a new tenant"""
    try:
        service = TenantService(db)
        # TODO: Pass current_user when auth is implemented
        tenant = await service.create_tenant(request)
        return ApiResponse(
            success=True,
            message="Tenant created successfully",
            data=tenant
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@tenant_router.get("/{tenant_id}", response_model=ApiResponse[TenantDetailResponse])
async def get_tenant(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get a specific tenant by ID"""
    try:
        service = TenantService(db)
        tenant = await service.get_tenant_by_id(tenant_id)
        if not tenant:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
        
        return ApiResponse(
            success=True,
            message="Tenant retrieved successfully",
            data=tenant
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@tenant_router.get("", response_model=ApiResponse[TenantCollectionResponse])
async def list_tenants(
    request: ListRequestFilters = Depends(ListRequestFilters),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[TenantCollectionResponse]:
    """Get paginated list of tenants"""
    try:
        service = TenantService(db)
     
        result = await service.get_tenants_paginated(request)
        
        return ApiResponse(
            success=True,
            message="Tenants retrieved successfully",
            data=TenantCollectionResponse(
               data = result.data
            ),
            paginations=result.pagination
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@tenant_router.put("/{tenant_id}", response_model=ApiResponse[TenantDetailResponse])
async def update_tenant(
    tenant_id: UUID,
    request: TenantUpdateRequest,
    db: AsyncSession = Depends(get_db),
    # TODO: Add current_user parameter when auth dependency is available
) -> dict:
    """Update an existing tenant"""
    try:
        service = TenantService(db)
        # TODO: Pass current_user when auth is implemented
        tenant = await service.update_tenant(tenant_id, request)
        
        return ApiResponse(
            success=True,
            message="Tenant updated successfully",
            data=tenant
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@tenant_router.delete("/{tenant_id}", response_model=ApiResponse[TenantDetailResponse])
async def delete_tenant(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db),
    # TODO: Add current_user parameter when auth dependency is available
) -> dict:
    """Soft delete a tenant"""
    try:
        service = TenantService(db)
        # TODO: Pass current_user when auth is implemented
        tenant = await service.delete_tenant(tenant_id)
        
        return ApiResponse(
            success=True,
            message="Tenant deleted successfully",
            data=tenant
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@tenant_router.post("/{tenant_id}/restore", response_model=ApiResponse[TenantDetailResponse])
async def restore_tenant(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Restore a soft-deleted tenant"""
    try:
        service = TenantService(db)
        tenant = await service.restore_tenant(tenant_id)
        
        return ApiResponse(
            success=True,
            message="Tenant restored successfully",
            data=tenant
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@tenant_router.patch("/{tenant_id}/status", response_model=ApiResponse[TenantDetailResponse])
async def toggle_tenant_status(
    tenant_id: UUID,
    is_active: bool = Query(..., description="New status"),
    db: AsyncSession = Depends(get_db),
    # TODO: Add current_user parameter when auth dependency is available
) -> dict:
    """Toggle tenant active/inactive status"""
    try:
        service = TenantService(db)
        # TODO: Pass current_user when auth is implemented
        tenant = await service.toggle_tenant_status(tenant_id, is_active)
        
        return ApiResponse(
            success=True,
            message="Tenant status updated successfully",
            data=tenant
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
