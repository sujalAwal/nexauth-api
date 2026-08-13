import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from alembic import context

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from app.database import Base
from app.modules.users.models.users import User
from app.modules.setting_groups.models.setting_group import SettingGroup
from app.modules.settings.models.setting import Setting
from app.modules.brands.models.brand import Brand
from app.modules.categories.models.category import Category
from app.modules.products.models.product import Product
from app.modules.email_templates.models.email_template import EmailTemplate
from app.modules.tenant.models.tenant import Tenant
from app.modules.tenant_services.models.tenant_service import TenantService
from app.modules.master_data.models.master_data import MasterData
from app.modules.master_data_items.models.master_data_items import MasterDataItem
from app.modules.chatbot.models.chatbot import Document, DocumentChunk , Conversation , Message , ChatFeedback   
from app.modules.chatbot.models.sharepoint import Sharepoint
from app.modules.department.models.department import Department, DepartmentSharepointLink, DepartmentPermission

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    from app.database import engine
    print("DEBUG ENGINE URL:", engine.url)
    print("DEBUG ENGINE URL HOST:", engine.url.host)
    print("DEBUG ENGINE URL PORT:", engine.url.port)
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)


def do_run_migrations(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()