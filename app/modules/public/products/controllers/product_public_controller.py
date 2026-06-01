from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from decimal import Decimal
from app.database import get_db
from app.modules.public.products.services.product_public_service import ProductPublicService
from app.modules.public.products.schemas.response.product_public_response import (
    ProductPublicBasicResponse,
    ProductPublicFullResponse,
    ProductPublicBasicCollection
)
from app.schemas.response import ApiResponse

product_public_router = APIRouter()


@product_public_router.get("/", response_model=ApiResponse[ProductPublicBasicCollection])
def list_products(
    search: str = None,
    category_id: UUID = None,
    brand_id: UUID = None,
    min_price: Decimal = None,
    max_price: Decimal = None,
    in_stock_only: bool = False,
    db: Session = Depends(get_db)
):
    """Get all active products (public endpoint) with advanced filtering."""
    try:
        service = ProductPublicService(db)
        products = service.search_products(
            search=search,
            category_id=category_id,
            brand_id=brand_id,
            min_price=min_price,
            max_price=max_price,
            in_stock_only=in_stock_only
        )
        
        return ApiResponse(
            success=True,
            message="Products retrieved successfully",
            data=ProductPublicBasicCollection(data=[ProductPublicBasicResponse.model_validate(p) for p in products])
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@product_public_router.get("/featured", response_model=ApiResponse[ProductPublicBasicCollection])
def get_featured_products(db: Session = Depends(get_db)):
    """Get featured products (public endpoint)."""
    try:
        service = ProductPublicService(db)
        products = service.get_featured_products()
        
        return ApiResponse(
            success=True,
            message="Featured products retrieved successfully",
            data=ProductPublicBasicCollection(data=[ProductPublicBasicResponse.model_validate(p) for p in products])
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@product_public_router.get("/sale", response_model=ApiResponse[ProductPublicBasicCollection])
def get_sale_products(db: Session = Depends(get_db)):
    """Get products on sale (public endpoint)."""
    try:
        service = ProductPublicService(db)
        products = service.get_on_sale_products()
        
        return ApiResponse(
            success=True,
            message="Sale products retrieved successfully",
            data=ProductPublicBasicCollection(data=[ProductPublicBasicResponse.model_validate(p) for p in products])
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@product_public_router.get("/category/{category_id}", response_model=ApiResponse[ProductPublicBasicCollection])
def get_products_by_category(category_id: UUID, db: Session = Depends(get_db)):
    """Get products by category (public endpoint)."""
    try:
        service = ProductPublicService(db)
        products = service.get_products_by_category(category_id)
        
        return ApiResponse(
            success=True,
            message="Category products retrieved successfully",
            data=ProductPublicBasicCollection(data=[ProductPublicBasicResponse.model_validate(p) for p in products])
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@product_public_router.get("/brand/{brand_id}", response_model=ApiResponse[ProductPublicBasicCollection])
def get_products_by_brand(brand_id: UUID, db: Session = Depends(get_db)):
    """Get products by brand (public endpoint)."""
    try:
        service = ProductPublicService(db)
        products = service.get_products_by_brand(brand_id)
        
        return ApiResponse(
            success=True,
            message="Brand products retrieved successfully",
            data=ProductPublicBasicCollection(data=[ProductPublicBasicResponse.model_validate(p) for p in products])
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@product_public_router.get("/{product_id}", response_model=ApiResponse[ProductPublicFullResponse])
def get_product_by_id(product_id: UUID, db: Session = Depends(get_db)):
    """Get product details by ID (public endpoint - full details with incremented visit count)."""
    try:
        service = ProductPublicService(db)
        product = service.get_product_by_id(product_id)
        
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        
        # Increment visit count
        service.increment_visit_count(product_id)
        
        return ApiResponse(
            success=True,
            message="Product retrieved successfully",
            data=ProductPublicFullResponse.model_validate(product)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@product_public_router.get("/by-name/{name}", response_model=ApiResponse[ProductPublicFullResponse])
def get_product_by_name(name: str, db: Session = Depends(get_db)):
    """Get product by name/slug (public endpoint - full details)."""
    try:
        service = ProductPublicService(db)
        product = service.get_product_by_name(name)
        
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        
        return ApiResponse(
            success=True,
            message="Product retrieved successfully",
            data=ProductPublicFullResponse.model_validate(product)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
