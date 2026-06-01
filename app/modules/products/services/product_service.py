from sqlalchemy.orm import Session
from uuid import UUID
from app.modules.products.repositories.product_repository import ProductRepository
from app.modules.products.schemas.requests.product_request import ProductCreateRequest, ProductUpdateRequest
from app.utils.models.mixin.pagination_query_handler import PaginationQueryHandler
from app.modules.products.models.product import Product
from datetime import datetime, timezone


class ProductService:
    """Service for product business logic."""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = ProductRepository(db)
    
    def create_product(self, product_request: ProductCreateRequest, created_by: str) -> Product:
        """Create a new product with validation."""
        # Validate unique name (slug)
        if self.repo.name_exists(product_request.name):
            raise ValueError(f"Product with name '{product_request.name}' already exists")
        
        # Validate unique SKU
        if self.repo.sku_exists(product_request.sku):
            raise ValueError(f"Product with SKU '{product_request.sku}' already exists")
        
        product_data = product_request.model_dump()
        product_data["created_by"] = created_by
        product_data["updated_by"] = created_by
        # Convert UUID to string for storage
        product_data["category_id"] = str(product_request.category_id)
        if product_request.brand_id:
            product_data["brand_id"] = str(product_request.brand_id)
        
        return self.repo.create(product_data)
    
    def get_product_by_id(self, product_id: UUID) -> Product | None:
        """Get a product by ID and increment visit count."""
        product = self.repo.get_by_id(product_id)
        if product:
            self.repo.increment_visit_count(product_id)
        return product
    
    def get_product_by_name(self, name: str) -> Product | None:
        """Get a product by name (URL slug)."""
        return self.repo.get_by_name(name)
    
    def get_product_by_sku(self, sku: str) -> Product | None:
        """Get a product by SKU."""
        return self.repo.get_by_sku(sku)
    
    def get_products_by_category(self, category_id: UUID) -> list[Product]:
        """Get all products in a category."""
        return self.repo.get_by_category(str(category_id))
    
    def get_products_by_brand(self, brand_id: UUID) -> list[Product]:
        """Get all products by brand."""
        return self.repo.get_by_brand(str(brand_id))
    
    def get_featured_products(self) -> list[Product]:
        """Get all featured active products."""
        return self.repo.get_featured()
    
    def get_products_on_sale(self) -> list[Product]:
        """Get all products on sale/discount."""
        return self.repo.get_on_sale()
    
    def get_low_stock_products(self) -> list[Product]:
        """Get all products with low stock."""
        return self.repo.get_low_stock()
    
    def update_product(self, product_id: UUID, product_request: ProductUpdateRequest, updated_by: str) -> Product:
        """Update an existing product with validation."""
        product = self.repo.get_by_id(product_id)
        if not product:
            raise ValueError(f"Product with ID '{product_id}' not found")
        
        # Validate unique name if changing it
        if product_request.name and product_request.name != product.name:
            if self.repo.name_exists(product_request.name, exclude_id=product_id):
                raise ValueError(f"Product with name '{product_request.name}' already exists")
        
        # Validate unique SKU if changing it
        if product_request.sku and product_request.sku != product.sku:
            if self.repo.sku_exists(product_request.sku, exclude_id=product_id):
                raise ValueError(f"Product with SKU '{product_request.sku}' already exists")
        
        product_data = product_request.model_dump(exclude_unset=True)
        product_data["updated_by"] = updated_by
        product_data["updated_at"] = datetime.now(timezone.utc)
        
        # Convert UUIDs to strings if provided
        if product_request.category_id:
            product_data["category_id"] = str(product_request.category_id)
        if product_request.brand_id:
            product_data["brand_id"] = str(product_request.brand_id)
        
        return self.repo.update(product_id, product_data)
    
    def delete_product(self, product_id: UUID, deleted_by: str) -> Product:
        """Soft delete a product."""
        product = self.repo.get_by_id(product_id)
        if not product:
            raise ValueError(f"Product with ID '{product_id}' not found")
        
        return self.repo.delete(product_id, deleted_by)
    
    def get_products_paginated(self, search: str = None, sort: str = None, 
                              page: int = 1, limit: int = 10) -> dict:
        """Get products with pagination and filtering."""
        query = self.db.query(Product)
        
        handler = PaginationQueryHandler(
            query=query,
            model=Product,
            searchable_fields=[Product.name, Product.title, Product.sku, Product.mpn],
            search=search,
            sort=sort,
            page=page,
            limit=limit
        )
        
        return handler.get_paginated_response()
