from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.modules.public.categories.services.category_public_service import CategoryPublicService
from app.modules.public.categories.schemas.response.category_public_response import CategoryPublicResponse, CategoryPublicCollection
from app.schemas.response import ApiResponse

category_public_router = APIRouter()


@category_public_router.get("/", response_model=ApiResponse[CategoryPublicCollection])
def list_categories(db: Session = Depends(get_db)):
    """Get all active categories (public endpoint)."""
    try:
        service = CategoryPublicService(db)
        categories = service.get_all_active_categories()
        
        return ApiResponse(
            success=True,
            message="Categories retrieved successfully",
            data=CategoryPublicCollection(data=[CategoryPublicResponse.model_validate(cat) for cat in categories])
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@category_public_router.get("/featured", response_model=ApiResponse[CategoryPublicCollection])
def get_featured_categories(db: Session = Depends(get_db)):
    """Get featured categories (public endpoint)."""
    try:
        service = CategoryPublicService(db)
        categories = service.get_featured_categories()
        
        return ApiResponse(
            success=True,
            message="Featured categories retrieved successfully",
            data=CategoryPublicCollection(data=[CategoryPublicResponse.model_validate(cat) for cat in categories])
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@category_public_router.get("/{name}", response_model=ApiResponse[CategoryPublicResponse])
def get_category_by_name(name: str, db: Session = Depends(get_db)):
    """Get category by name (public endpoint)."""
    try:
        service = CategoryPublicService(db)
        category = service.get_category_by_name(name)
        
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        
        return ApiResponse(
            success=True,
            message="Category retrieved successfully",
            data=CategoryPublicResponse.model_validate(category)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
