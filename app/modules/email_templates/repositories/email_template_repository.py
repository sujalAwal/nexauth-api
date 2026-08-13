"""EmailTemplate Repository - Database access layer"""
from datetime import datetime, timezone
from sqlalchemy import select, exists as sa_exists
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.modules.email_templates.models.email_template import EmailTemplate


class EmailTemplateRepository:
    """Handles all database operations for email templates"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, template_id: UUID) -> EmailTemplate | None:
        result = await self.db.execute(select(EmailTemplate).where(EmailTemplate.id == template_id))
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> EmailTemplate | None:
        result = await self.db.execute(select(EmailTemplate).where(EmailTemplate.name == name))
        return result.scalar_one_or_none()

    async def name_exists(self, name: str) -> bool:
        inner = select(EmailTemplate.id).where(EmailTemplate.name == name)
        result = await self.db.execute(select(inner.exists()))
        return result.scalar()

    async def get_all_active(self) -> list[EmailTemplate]:
        query = select(EmailTemplate).where(EmailTemplate.is_active == True)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create(self, template: EmailTemplate) -> EmailTemplate:
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)
        return template

    async def update(self, template: EmailTemplate) -> EmailTemplate:
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)
        return template

    async def delete(self, template_id: UUID, deleted_by: UUID) -> bool:
        template = await self.get_by_id(template_id)
        if template:
            template.deleted_at = datetime.now(timezone.utc)
            template.deleted_by = deleted_by
            self.db.add(template)
            await self.db.commit()
            return True
        return False
