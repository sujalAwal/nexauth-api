from sqlalchemy.orm import Session
from app.modules.categories.models.category import Category


class CategoryPublicService:
    """Service for public category operations (read-only)."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_active_categories(self) -> list[Category]:
        """Get all active categories ordered by display_order."""
        return self.db.query(Category).filter(
            Category.is_active == True
        ).order_by(Category.display_order).all()
    
    def get_category_by_name(self, name: str) -> Category | None:
        """Get category by name."""
        return self.db.query(Category).filter(
            Category.name == name,
            Category.is_active == True
        ).first()
    
    def get_featured_categories(self) -> list[Category]:
        """Get featured categories."""
        return self.db.query(Category).filter(
            Category.is_featured == True,
            Category.is_active == True
        ).order_by(Category.display_order).all()
