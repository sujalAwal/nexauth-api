from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID
from datetime import datetime, timezone
from app.modules.brands.models.brand import Brand


class BrandRepository:
    """Repository for brand database operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, brand_id: UUID) -> Brand | None:
        """Get brand by ID."""
        return self.db.query(Brand).filter(Brand.id == brand_id).first()
    
    def get_by_name(self, name: str) -> Brand | None:
        """Get brand by name."""
        return self.db.query(Brand).filter(Brand.name == name).first()
    
    def name_exists(self, name: str, exclude_id: UUID = None) -> bool:
        """Check if brand name already exists."""
        query = self.db.query(Brand.name).where(Brand.name == name)
        if exclude_id:
            query = query.where(Brand.id != exclude_id)
        return query.first() is not None
    
    def get_all_active(self) -> list[Brand]:
        """Get all active brands."""
        return self.db.query(Brand).filter(Brand.is_active == True).all()
    
    def get_featured(self) -> list[Brand]:
        """Get all featured brands."""
        return self.db.query(Brand).filter(
            Brand.is_featured == True,
            Brand.is_active == True
        ).all()
    
    def increment_visit_count(self, brand_id: UUID) -> None:
        """Increment visit count for a brand."""
        brand = self.get_by_id(brand_id)
        if brand:
            brand.visit_count += 1
            self.db.add(brand)
            self.db.commit()
    
    def create(self, brand_data: dict) -> Brand:
        """Create a new brand."""
        brand = Brand(**brand_data)
        self.db.add(brand)
        self.db.commit()
        self.db.refresh(brand)
        return brand
    
    def update(self, brand_id: UUID, brand_data: dict) -> Brand | None:
        """Update an existing brand."""
        brand = self.get_by_id(brand_id)
        if not brand:
            return None
        
        for key, value in brand_data.items():
            if value is not None and hasattr(brand, key):
                setattr(brand, key, value)
        
        self.db.add(brand)
        self.db.commit()
        self.db.refresh(brand)
        return brand
    
    def delete(self, brand_id: UUID, deleted_by: str) -> Brand | None:
        """Soft delete a brand."""
        brand = self.get_by_id(brand_id)
        if not brand:
            return None
        
        brand.deleted_at = datetime.now(timezone.utc)
        brand.deleted_by = deleted_by
        
        self.db.add(brand)
        self.db.commit()
        self.db.refresh(brand)
        return brand
    
    def get_all(self, skip: int = 0, limit: int = 10) -> list[Brand]:
        """Get all brands with pagination."""
        return self.db.query(Brand).offset(skip).limit(limit).all()
    
    def count(self) -> int:
        """Get total count of non-deleted brands."""
        return self.db.query(func.count(Brand.id)).scalar()
