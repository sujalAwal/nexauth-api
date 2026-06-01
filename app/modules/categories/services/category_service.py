from sqlalchemy.orm import Session
from uuid import UUID
from app.modules.categories.repositories.category_repository import CategoryRepository
from app.modules.categories.schemas.requests.category_request import CategoryCreateRequest, CategoryUpdateRequest
from app.utils.models.mixin.pagination_query_handler import PaginationQueryHandler
from app.modules.categories.models.category import Category
from datetime import datetime, timezone


class CategoryService:
    """Service for category business logic."""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = CategoryRepository(db)
    
    def create_category(self, category_request: CategoryCreateRequest, created_by: str) -> Category:
        """Create a new category with validation."""
        # Validate unique name
        if self.repo.name_exists(category_request.name):
            raise ValueError(f"Category with name '{category_request.name}' already exists")
        
        category_data = category_request.model_dump()
        category_data["created_by"] = created_by
        category_data["updated_by"] = created_by
        
        return self.repo.create(category_data)
    
    def get_category_by_id(self, category_id: UUID) -> Category | None:
        """Get a category by ID."""
        return self.repo.get_by_id(category_id)
    
    def get_category_by_name(self, name: str) -> Category | None:
        """Get a category by name (URL slug)."""
        return self.repo.get_by_name(name)
    
    def get_featured_categories(self) -> list[Category]:
        """Get all featured active categories ordered by display_order."""
        return self.repo.get_featured()
    
    def update_category(self, category_id: UUID, category_request: CategoryUpdateRequest, updated_by: str) -> Category:
        """Update an existing category with validation."""
        category = self.repo.get_by_id(category_id)
        if not category:
            raise ValueError(f"Category with ID '{category_id}' not found")
        
        # Validate unique name if changing it
        if category_request.name and category_request.name != category.name:
            if self.repo.name_exists(category_request.name, exclude_id=category_id):
                raise ValueError(f"Category with name '{category_request.name}' already exists")
        
        category_data = category_request.model_dump(exclude_unset=True)
        category_data["updated_by"] = updated_by
        category_data["updated_at"] = datetime.now(timezone.utc)
        
        return self.repo.update(category_id, category_data)
    
    def delete_category(self, category_id: UUID, deleted_by: str) -> Category:
        """Soft delete a category."""
        category = self.repo.get_by_id(category_id)
        if not category:
            raise ValueError(f"Category with ID '{category_id}' not found")
        
        return self.repo.delete(category_id, deleted_by)
    
    def get_categories_paginated(self, search: str = None, sort: str = None, 
                                page: int = 1, limit: int = 10) -> dict:
        """Get categories with pagination and filtering."""
        query = self.db.query(Category)
        
        handler = PaginationQueryHandler(
            query=query,
            model=Category,
            searchable_fields=[Category.name, Category.title, Category.description],
            search=search,
            sort=sort,
            page=page,
            limit=limit
        )
        
        return handler.get_paginated_response()
