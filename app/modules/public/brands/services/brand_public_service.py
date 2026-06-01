from sqlalchemy.orm import Session
from app.modules.brands.models.brand import Brand


class BrandPublicService:
    """Service for public brand operations (read-only)."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_active_brands(self) -> list[Brand]:
        """Get all active brands for public display."""
        return self.db.query(Brand).filter(Brand.is_active == True).all()
    
    def get_brand_by_name(self, name: str) -> Brand | None:
        """Get brand by name."""
        return self.db.query(Brand).filter(
            Brand.name == name,
            Brand.is_active == True
        ).first()
