from sqlalchemy.orm import Session
from uuid import UUID
from decimal import Decimal
from app.modules.products.models.product import Product


class ProductPublicService:
    """Service for public product operations (read-only with advanced filtering)."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_featured_products(self) -> list[Product]:
        """Get all featured active products."""
        return self.db.query(Product).filter(
            Product.is_featured == True,
            Product.is_active == True
        ).order_by(Product.display_order).all()
    
    def get_on_sale_products(self) -> list[Product]:
        """Get all products on sale/discount."""
        return self.db.query(Product).filter(
            Product.is_discount == True,
            Product.is_active == True
        ).order_by(Product.display_order).all()
    
    def get_products_by_category(self, category_id: UUID) -> list[Product]:
        """Get all products in a category."""
        return self.db.query(Product).filter(
            Product.category_id == str(category_id),
            Product.is_active == True
        ).order_by(Product.display_order).all()
    
    def get_products_by_brand(self, brand_id: UUID) -> list[Product]:
        """Get all products by a brand."""
        return self.db.query(Product).filter(
            Product.brand_id == str(brand_id),
            Product.is_active == True
        ).order_by(Product.display_order).all()
    
    def search_products(
        self,
        search: str = None,
        category_id: UUID = None,
        brand_id: UUID = None,
        min_price: Decimal = None,
        max_price: Decimal = None,
        in_stock_only: bool = False
    ) -> list[Product]:
        """Search products with multiple filters."""
        query = self.db.query(Product).filter(Product.is_active == True)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (Product.title.ilike(search_term)) |
                (Product.name.ilike(search_term)) |
                (Product.sku.ilike(search_term))
            )
        
        if category_id:
            query = query.filter(Product.category_id == str(category_id))
        
        if brand_id:
            query = query.filter(Product.brand_id == str(brand_id))
        
        if min_price is not None:
            query = query.filter(Product.price >= min_price)
        
        if max_price is not None:
            query = query.filter(Product.price <= max_price)
        
        if in_stock_only:
            query = query.filter(Product.stock_quantity > 0)
        
        return query.order_by(Product.display_order).all()
    
    def get_product_by_id(self, product_id: UUID) -> Product | None:
        """Get product by ID (public view)."""
        return self.db.query(Product).filter(
            Product.id == product_id,
            Product.is_active == True
        ).first()
    
    def get_product_by_name(self, name: str) -> Product | None:
        """Get product by name/slug (public view)."""
        return self.db.query(Product).filter(
            Product.name == name,
            Product.is_active == True
        ).first()
    
    def increment_visit_count(self, product_id: UUID) -> None:
        """Increment visit count for a product."""
        product = self.get_product_by_id(product_id)
        if product:
            product.visit_count += 1
            self.db.add(product)
            self.db.commit()
