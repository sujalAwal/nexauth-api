from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.modules.public.brands.services.brand_public_service import BrandPublicService
from app.modules.public.brands.schemas.response.brand_public_response import BrandPublicResponse, BrandPublicCollection
from app.schemas.response import ApiResponse

brand_public_router = APIRouter()


@brand_public_router.get("/", response_model=ApiResponse[BrandPublicCollection])
async def list_brands(db: AsyncSession = Depends(get_db)):
    """Get all active brands (public endpoint)."""
    try:
        service = BrandPublicService(db)
        brands = await service.get_all_active_brands()

        return ApiResponse(
            success=True,
            message="Brands retrieved successfully",
            data=BrandPublicCollection(data=[BrandPublicResponse.model_validate(brand) for brand in brands]),
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@brand_public_router.get("/{name}", response_model=ApiResponse[BrandPublicResponse])
async def get_brand_by_name(name: str, db: AsyncSession = Depends(get_db)):
    """Get brand by name (public endpoint)."""
    try:
        service = BrandPublicService(db)
        brand = await service.get_brand_by_name(name)

        if not brand:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")

        return ApiResponse(
            success=True,
            message="Brand retrieved successfully",
            data=BrandPublicResponse.model_validate(brand),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
