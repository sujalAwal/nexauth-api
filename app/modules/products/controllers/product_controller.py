from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from app.database import get_db
from app.modules.products.services import ProductService
from app.modules.products.schemas.requests.product_request import ProductCreateRequest, ProductUpdateRequest
from app.modules.products.schemas.response.product_response import ProductResponse, ProductCollection
from app.schemas.response import ApiResponse
from app.schemas.pagination_response import PaginationResponse

product_router = APIRouter()


@product_router.get("/", response_model=ApiResponse[ProductCollection])
def list_products(
    search: str = None,
    sort: str = None,
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get all products with pagination and search."""
    try:
        service = ProductService(db)
        result = service.get_products_paginated(search=search, sort=sort, page=page, limit=limit)
        
        products = [ProductResponse.model_validate(product) for product in result["data"]]
        return ApiResponse(
            success=True,
            message="Products retrieved successfully",
            data=ProductCollection(data=products),
            paginations=result.get("pagination")
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@product_router.get("/{product_id}", response_model=ApiResponse[ProductResponse])
def get_product(
    product_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a single product by ID (increments visit count)."""
    try:
        service = ProductService(db)
        product = service.get_product_by_id(product_id)
        
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        
        return ApiResponse(
            success=True,
            message="Product retrieved successfully",
            data=ProductResponse.model_validate(product)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@product_router.get("/by-name/{name}", response_model=ApiResponse[ProductResponse])
def get_product_by_name(
    name: str,
    db: Session = Depends(get_db)
):
    """Get a product by name (URL slug)."""
    try:
        service = ProductService(db)
        product = service.get_product_by_name(name)
        
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        
        return ApiResponse(
            success=True,
            message="Product retrieved successfully",
            data=ProductResponse.model_validate(product)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@product_router.get("/by-sku/{sku}", response_model=ApiResponse[ProductResponse])
def get_product_by_sku(
    sku: str,
    db: Session = Depends(get_db)
):
    """Get a product by SKU."""
    try:
        service = ProductService(db)
        product = service.get_product_by_sku(sku)
        
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        
        return ApiResponse(
            success=True,
            message="Product retrieved successfully",
            data=ProductResponse.model_validate(product)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@product_router.get("/category/{category_id}", response_model=ApiResponse[ProductCollection])
def get_products_by_category(
    category_id: UUID,
    db: Session = Depends(get_db)
):
    """Get all products in a category."""
    try:
        service = ProductService(db)
        products = service.get_products_by_category(category_id)
        
        return ApiResponse(
            success=True,
            message="Category products retrieved successfully",
            data=ProductCollection(data=[ProductResponse.model_validate(p) for p in products])
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@product_router.get("/brand/{brand_id}", response_model=ApiResponse[ProductCollection])
def get_products_by_brand(
    brand_id: UUID,
    db: Session = Depends(get_db)
):
    """Get all products by a brand."""
    try:
        service = ProductService(db)
        products = service.get_products_by_brand(brand_id)
        
        return ApiResponse(
            success=True,
            message="Brand products retrieved successfully",
            data=ProductCollection(data=[ProductResponse.model_validate(p) for p in products])
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@product_router.get("/featured/list", response_model=ApiResponse[ProductCollection])
def get_featured_products(
    db: Session = Depends(get_db)
):
    """Get all featured active products."""
    try:
        service = ProductService(db)
        products = service.get_featured_products()
        
        return ApiResponse(
            success=True,
            message="Featured products retrieved successfully",
            data=ProductCollection(data=[ProductResponse.model_validate(p) for p in products])
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@product_router.get("/sale/list", response_model=ApiResponse[ProductCollection])
def get_products_on_sale(
    db: Session = Depends(get_db)
):
    """Get all products on sale/discount."""
    try:
        service = ProductService(db)
        products = service.get_products_on_sale()
        
        return ApiResponse(
            success=True,
            message="Sale products retrieved successfully",
            data=ProductCollection(data=[ProductResponse.model_validate(p) for p in products])
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@product_router.post("/", response_model=ApiResponse[ProductResponse], status_code=status.HTTP_201_CREATED)
def create_product(
    product_request: ProductCreateRequest,
    db: Session = Depends(get_db)
):
    """Create a new product."""
    try:
        service = ProductService(db)
        product = service.create_product(product_request, created_by=str(UUID(int=0)))
        
        return ApiResponse(
            success=True,
            message="Product created successfully",
            data=ProductResponse.model_validate(product)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@product_router.put("/{product_id}", response_model=ApiResponse[ProductResponse])
def update_product(
    product_id: UUID,
    product_request: ProductUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update an existing product."""
    try:
        service = ProductService(db)
        product = service.update_product(product_id, product_request, updated_by=str(UUID(int=0)))
        
        return ApiResponse(
            success=True,
            message="Product updated successfully",
            data=ProductResponse.model_validate(product)
        )
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@product_router.delete("/{product_id}", response_model=ApiResponse[ProductResponse])
def delete_product(
    product_id: UUID,
    db: Session = Depends(get_db)
):
    """Soft delete a product."""
    try:
        service = ProductService(db)
        product = service.delete_product(product_id, deleted_by=str(UUID(int=0)))
        
        return ApiResponse(
            success=True,
            message="Product deleted successfully",
            data=ProductResponse.model_validate(product)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
