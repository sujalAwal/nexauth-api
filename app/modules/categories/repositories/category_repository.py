from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID
from datetime import datetime, timezone
from app.modules.categories.models.category import Category


class CategoryRepository:
    """Repository for category database operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, category_id: UUID) -> Category | None:
        """Get category by ID."""
        return self.db.query(Category).filter(Category.id == category_id).first()
    
    def get_by_name(self, name: str) -> Category | None:
        """Get category by name (URL slug)."""
        return self.db.query(Category).filter(Category.name == name).first()
    
    def name_exists(self, name: str, exclude_id: UUID = None) -> bool:
        """Check if category name already exists."""
        query = self.db.query(Category.name).where(Category.name == name)
        if exclude_id:
            query = query.where(Category.id != exclude_id)
        return query.first() is not None
    
    def get_all_active(self) -> list[Category]:
        """Get all active categories ordered by display_order."""
        return self.db.query(Category).filter(
            Category.is_active == True
        ).order_by(Category.display_order).all()
    
    def get_featured(self) -> list[Category]:
        """Get all featured active categories."""
        return self.db.query(Category).filter(
            Category.is_featured == True,
            Category.is_active == True
        ).order_by(Category.display_order).all()
    
    def create(self, category_data: dict) -> Category:
        """Create a new category."""
        category = Category(**category_data)
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category
    
    def update(self, category_id: UUID, category_data: dict) -> Category | None:
        """Update an existing category."""
        category = self.get_by_id(category_id)
        if not category:
            return None
        
        for key, value in category_data.items():
            if value is not None and hasattr(category, key):
                setattr(category, key, value)
        
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category
    
    def delete(self, category_id: UUID, deleted_by: str) -> Category | None:
        """Soft delete a category."""
        category = self.get_by_id(category_id)
        if not category:
            return None
        
        category.deleted_at = datetime.now(timezone.utc)
        category.deleted_by = deleted_by
        
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category
    
    def get_all(self, skip: int = 0, limit: int = 10) -> list[Category]:
        """Get all categories with pagination."""
        return self.db.query(Category).offset(skip).limit(limit).all()
    
    def count(self) -> int:
        """Get total count of non-deleted categories."""
        return self.db.query(func.count(Category.id)).scalar()
