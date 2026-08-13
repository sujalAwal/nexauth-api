from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.database import get_db
from app.modules.brands.services import BrandService
from app.modules.brands.schemas.requests.brand_request import BrandCreateRequest, BrandUpdateRequest
from app.modules.brands.schemas.response.brand_response import BrandResponse, BrandCollection
from app.schemas.response import ApiResponse

brand_router = APIRouter()


@brand_router.get("/", response_model=ApiResponse[BrandCollection])
async def list_brands(
    search: str = None,
    sort: str = None,
    page: int = 1,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """Get all brands with pagination and search."""
    try:
        service = BrandService(db)
        result = await service.get_brands_paginated(search=search, sort=sort, page=page, limit=limit)

        brands = [BrandResponse.model_validate(brand) for brand in result["data"]]
        return ApiResponse(
            success=True,
            message="Brands retrieved successfully",
            data=BrandCollection(data=brands),
            paginations=result.get("pagination"),
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@brand_router.get("/{brand_id}", response_model=ApiResponse[BrandResponse])
async def get_brand(
    brand_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a single brand by ID."""
    try:
        service = BrandService(db)
        brand = await service.get_brand_by_id(brand_id)

        if not brand:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")

        await service.increment_visit_count(brand_id)

        return ApiResponse(
            success=True,
            message="Brand retrieved successfully",
            data=BrandResponse.model_validate(brand),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@brand_router.get("/by-name/{name}", response_model=ApiResponse[BrandResponse])
async def get_brand_by_name(
    name: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a brand by name."""
    try:
        service = BrandService(db)
        brand = await service.get_brand_by_name(name)

        if not brand:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")

        return ApiResponse(
            success=True,
            message="Brand retrieved successfully",
            data=BrandResponse.model_validate(brand),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@brand_router.post("/", response_model=ApiResponse[BrandResponse], status_code=status.HTTP_201_CREATED)
async def create_brand(
    brand_request: BrandCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new brand."""
    try:
        service = BrandService(db)
        brand = await service.create_brand(brand_request, created_by=UUID(int=0))

        return ApiResponse(
            success=True,
            message="Brand created successfully",
            data=BrandResponse.model_validate(brand),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@brand_router.put("/{brand_id}", response_model=ApiResponse[BrandResponse])
async def update_brand(
    brand_id: UUID,
    brand_request: BrandUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Update an existing brand."""
    try:
        service = BrandService(db)
        brand = await service.update_brand(brand_id, brand_request, updated_by=UUID(int=0))

        return ApiResponse(
            success=True,
            message="Brand updated successfully",
            data=BrandResponse.model_validate(brand),
        )
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@brand_router.delete("/{brand_id}", response_model=ApiResponse[BrandResponse])
async def delete_brand(
    brand_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Soft delete a brand."""
    try:
        service = BrandService(db)
        brand = await service.delete_brand(brand_id, deleted_by=UUID(int=0))

        return ApiResponse(
            success=True,
            message="Brand deleted successfully",
            data=BrandResponse.model_validate(brand),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
