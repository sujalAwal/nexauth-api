from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from app.database import get_db
from app.modules.categories.services import CategoryService
from app.modules.categories.schemas.requests.category_request import CategoryCreateRequest, CategoryUpdateRequest
from app.modules.categories.schemas.response.category_response import CategoryResponse, CategoryCollection
from app.schemas.response import ApiResponse
from app.schemas.pagination_response import PaginationResponse

category_router = APIRouter()


@category_router.get("/", response_model=ApiResponse[CategoryCollection])
def list_categories(
    search: str = None,
    sort: str = None,
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get all categories with pagination and search."""
    try:
        service = CategoryService(db)
        result = service.get_categories_paginated(search=search, sort=sort, page=page, limit=limit)
        
        categories = [CategoryResponse.model_validate(category) for category in result["data"]]
        return ApiResponse(
            success=True,
            message="Categories retrieved successfully",
            data=CategoryCollection(data=categories),
            paginations=result.get("pagination")
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@category_router.get("/{category_id}", response_model=ApiResponse[CategoryResponse])
def get_category(
    category_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a single category by ID."""
    try:
        service = CategoryService(db)
        category = service.get_category_by_id(category_id)
        
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        
        return ApiResponse(
            success=True,
            message="Category retrieved successfully",
            data=CategoryResponse.model_validate(category)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@category_router.get("/by-name/{name}", response_model=ApiResponse[CategoryResponse])
def get_category_by_name(
    name: str,
    db: Session = Depends(get_db)
):
    """Get a category by name (URL slug)."""
    try:
        service = CategoryService(db)
        category = service.get_category_by_name(name)
        
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        
        return ApiResponse(
            success=True,
            message="Category retrieved successfully",
            data=CategoryResponse.model_validate(category)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@category_router.post("/", response_model=ApiResponse[CategoryResponse], status_code=status.HTTP_201_CREATED)
def create_category(
    category_request: CategoryCreateRequest,
    db: Session = Depends(get_db)
):
    """Create a new category."""
    try:
        service = CategoryService(db)
        category = service.create_category(category_request, created_by=str(UUID(int=0)))
        
        return ApiResponse(
            success=True,
            message="Category created successfully",
            data=CategoryResponse.model_validate(category)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@category_router.put("/{category_id}", response_model=ApiResponse[CategoryResponse])
def update_category(
    category_id: UUID,
    category_request: CategoryUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update an existing category."""
    try:
        service = CategoryService(db)
        category = service.update_category(category_id, category_request, updated_by=str(UUID(int=0)))
        
        return ApiResponse(
            success=True,
            message="Category updated successfully",
            data=CategoryResponse.model_validate(category)
        )
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@category_router.delete("/{category_id}", response_model=ApiResponse[CategoryResponse])
def delete_category(
    category_id: UUID,
    db: Session = Depends(get_db)
):
    """Soft delete a category."""
    try:
        service = CategoryService(db)
        category = service.delete_category(category_id, deleted_by=str(UUID(int=0)))
        
        return ApiResponse(
            success=True,
            message="Category deleted successfully",
            data=CategoryResponse.model_validate(category)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
