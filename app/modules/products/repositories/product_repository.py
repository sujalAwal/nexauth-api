from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID
from datetime import datetime, timezone
from app.modules.products.models.product import Product


class ProductRepository:
    """Repository for product database operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, product_id: UUID) -> Product | None:
        """Get product by ID."""
        return self.db.query(Product).filter(Product.id == product_id).first()
    
    def get_by_name(self, name: str) -> Product | None:
        """Get product by name (URL slug)."""
        return self.db.query(Product).filter(Product.name == name).first()
    
    def get_by_sku(self, sku: str) -> Product | None:
        """Get product by SKU."""
        return self.db.query(Product).filter(Product.sku == sku).first()
    
    def name_exists(self, name: str, exclude_id: UUID = None) -> bool:
        """Check if product name (slug) already exists."""
        query = self.db.query(Product.name).where(Product.name == name)
        if exclude_id:
            query = query.where(Product.id != exclude_id)
        return query.first() is not None
    
    def sku_exists(self, sku: str, exclude_id: UUID = None) -> bool:
        """Check if SKU already exists."""
        query = self.db.query(Product.sku).where(Product.sku == sku)
        if exclude_id:
            query = query.where(Product.id != exclude_id)
        return query.first() is not None
    
    def get_by_category(self, category_id: str) -> list[Product]:
        """Get all products in a category."""
        return self.db.query(Product).filter(
            Product.category_id == category_id,
            Product.is_active == True
        ).order_by(Product.display_order).all()
    
    def get_by_brand(self, brand_id: str) -> list[Product]:
        """Get all products by brand."""
        return self.db.query(Product).filter(
            Product.brand_id == brand_id,
            Product.is_active == True
        ).order_by(Product.display_order).all()
    
    def get_featured(self) -> list[Product]:
        """Get all featured active products."""
        return self.db.query(Product).filter(
            Product.is_featured == True,
            Product.is_active == True
        ).order_by(Product.display_order).all()
    
    def get_on_sale(self) -> list[Product]:
        """Get all products on sale/discount."""
        return self.db.query(Product).filter(
            Product.is_discount == True,
            Product.is_active == True
        ).order_by(Product.display_order).all()
    
    def get_low_stock(self) -> list[Product]:
        """Get all products with low stock (below threshold)."""
        return self.db.query(Product).filter(
            Product.stock_quantity < Product.low_stock_threshold,
            Product.is_active == True
        ).all()
    
    def increment_visit_count(self, product_id: UUID) -> None:
        """Increment visit count for a product."""
        product = self.get_by_id(product_id)
        if product:
            product.visit_count += 1
            self.db.add(product)
            self.db.commit()
    
    def create(self, product_data: dict) -> Product:
        """Create a new product."""
        product = Product(**product_data)
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product
    
    def update(self, product_id: UUID, product_data: dict) -> Product | None:
        """Update an existing product."""
        product = self.get_by_id(product_id)
        if not product:
            return None
        
        for key, value in product_data.items():
            if value is not None and hasattr(product, key):
                setattr(product, key, value)
        
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product
    
    def delete(self, product_id: UUID, deleted_by: str) -> Product | None:
        """Soft delete a product."""
        product = self.get_by_id(product_id)
        if not product:
            return None
        
        product.deleted_at = datetime.now(timezone.utc)
        product.deleted_by = deleted_by
        
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product
    
    def get_all(self, skip: int = 0, limit: int = 10) -> list[Product]:
        """Get all products with pagination."""
        return self.db.query(Product).offset(skip).limit(limit).all()
    
    def count(self) -> int:
        """Get total count of non-deleted products."""
        return self.db.query(func.count(Product.id)).scalar()
