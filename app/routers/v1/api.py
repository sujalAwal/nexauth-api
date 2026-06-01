from fastapi import APIRouter
from app.modules.users.controllers.user_controller import user_router
from app.modules.setting_groups.controllers.setting_group_controller import setting_group_router
from app.modules.settings.controllers.setting_controller import setting_router
from app.modules.email_templates.controllers.email_template_controller import email_template_router
from app.modules.brands.controllers.brand_controller import brand_router
from app.modules.categories.controllers.category_controller import category_router
from app.modules.products.controllers.product_controller import product_router

api = APIRouter()

api.include_router(user_router, prefix="/users", tags=["users"])
api.include_router(setting_group_router, prefix="/setting-groups", tags=["setting-groups"])
api.include_router(setting_router, prefix="/settings", tags=["settings"])
api.include_router(email_template_router, prefix="/email-templates", tags=["email-templates"])
api.include_router(brand_router, prefix="/brands", tags=["brands"])
api.include_router(category_router, prefix="/categories", tags=["categories"])
api.include_router(product_router, prefix="/products", tags=["products"])