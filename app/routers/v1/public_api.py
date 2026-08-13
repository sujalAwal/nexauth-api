from fastapi import APIRouter
from app.modules.public.brands.controllers.brand_public_controller import brand_public_router
from app.modules.public.categories.controllers.category_public_controller import category_public_router
from app.modules.public.products.controllers.product_public_controller import product_public_router
from app.modules.public.settings.controllers.setting_public_controller import setting_public_router

public_api = APIRouter()

public_api.include_router(brand_public_router, prefix="/brands", tags=["public-brands"])
public_api.include_router(category_public_router, prefix="/categories", tags=["public-categories"])
public_api.include_router(product_public_router, prefix="/products", tags=["public-products"])
public_api.include_router(setting_public_router, prefix="/settings", tags=["public-settings"])
