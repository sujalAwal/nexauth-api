from sqlalchemy.orm import Session
from uuid import UUID
from app.modules.brands.repositories.brand_repository import BrandRepository
from app.modules.brands.schemas.requests.brand_request import BrandCreateRequest, BrandUpdateRequest
from app.utils.models.mixin.pagination_query_handler import PaginationQueryHandler
from app.modules.brands.models.brand import Brand
from datetime import datetime, timezone


class BrandService:
    """Service for brand business logic."""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = BrandRepository(db)
    
    def create_brand(self, brand_request: BrandCreateRequest, created_by: str) -> Brand:
        """Create a new brand with validation."""
        # Validate unique name
        if self.repo.name_exists(brand_request.name):
            raise ValueError(f"Brand with name '{brand_request.name}' already exists")
        
        brand_data = brand_request.model_dump()
        brand_data["created_by"] = created_by
        brand_data["updated_by"] = created_by
        
        return self.repo.create(brand_data)
    
    def get_brand_by_id(self, brand_id: UUID) -> Brand | None:
        """Get a brand by ID."""
        return self.repo.get_by_id(brand_id)
    
    def get_brand_by_name(self, name: str) -> Brand | None:
        """Get a brand by name."""
        return self.repo.get_by_name(name)
    
    def get_featured_brands(self) -> list[Brand]:
        """Get all featured active brands."""
        return self.repo.get_featured()
    
    def update_brand(self, brand_id: UUID, brand_request: BrandUpdateRequest, updated_by: str) -> Brand:
        """Update an existing brand with validation."""
        brand = self.repo.get_by_id(brand_id)
        if not brand:
            raise ValueError(f"Brand with ID '{brand_id}' not found")
        
        # Validate unique name if changing it
        if brand_request.name and brand_request.name != brand.name:
            if self.repo.name_exists(brand_request.name, exclude_id=brand_id):
                raise ValueError(f"Brand with name '{brand_request.name}' already exists")
        
        brand_data = brand_request.model_dump(exclude_unset=True)
        brand_data["updated_by"] = updated_by
        brand_data["updated_at"] = datetime.now(timezone.utc)
        
        return self.repo.update(brand_id, brand_data)
    
    def delete_brand(self, brand_id: UUID, deleted_by: str) -> Brand:
        """Soft delete a brand."""
        brand = self.repo.get_by_id(brand_id)
        if not brand:
            raise ValueError(f"Brand with ID '{brand_id}' not found")
        
        return self.repo.delete(brand_id, deleted_by)
    
    def increment_visit_count(self, brand_id: UUID) -> None:
        """Increment visit count for a brand."""
        brand = self.repo.get_by_id(brand_id)
        if not brand:
            raise ValueError(f"Brand with ID '{brand_id}' not found")
        
        self.repo.increment_visit_count(brand_id)
    
    def get_brands_paginated(self, search: str = None, sort: str = None, 
                           page: int = 1, limit: int = 10) -> dict:
        """Get brands with pagination and filtering."""
        query = self.db.query(Brand)
        
        handler = PaginationQueryHandler(
            query=query,
            model=Brand,
            searchable_fields=[Brand.name, Brand.title, Brand.country_of_origin],
            search=search,
            sort=sort,
            page=page,
            limit=limit
        )
        
        return handler.get_paginated_response()
