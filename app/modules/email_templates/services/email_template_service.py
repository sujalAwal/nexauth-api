"""EmailTemplate Service - Business logic layer"""
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.email_templates.models.email_template import EmailTemplate
from app.modules.email_templates.schemas.requests.email_template_request import (
    EmailTemplateCreateRequest,
    EmailTemplateUpdateRequest,
)
from app.modules.email_templates.schemas.response.email_template_response import EmailTemplateResponse
from app.modules.email_templates.repositories.email_template_repository import EmailTemplateRepository
from app.schemas.request import ListRequestFilters
from app.utils.models.mixin.pagination_query_handler import PaginationQueryHandler


class EmailTemplateService:
    """Handles business logic for email template operations"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = EmailTemplateRepository(db)
        self.query_handler = PaginationQueryHandler(db)

    async def create_email_template(self, request: EmailTemplateCreateRequest) -> EmailTemplateResponse:
        if await self.repo.name_exists(request.name):
            raise ValueError(f"Email template name '{request.name}' already exists")

        new_template = EmailTemplate(
            title=request.title,
            name=request.name,
            subject=request.subject,
            body=request.body,
            cc=request.cc,
            admin_subject=request.admin_subject,
            admin_body=request.admin_body,
            admin_cc=request.admin_cc,
            is_active=True,
            created_by=request.created_by,
            updated_by=request.created_by,
        )

        created_template = await self.repo.create(new_template)
        return EmailTemplateResponse.model_validate(created_template)

    async def get_email_template_by_id(self, template_id: UUID) -> EmailTemplateResponse | None:
        template = await self.repo.get_by_id(template_id)
        if template:
            return EmailTemplateResponse.model_validate(template)
        return None

    async def get_email_template_by_name(self, name: str) -> EmailTemplateResponse | None:
        template = await self.repo.get_by_name(name)
        if template:
            return EmailTemplateResponse.model_validate(template)
        return None

    async def update_email_template(self, template_id: UUID, request: EmailTemplateUpdateRequest) -> EmailTemplateResponse:
        template = await self.repo.get_by_id(template_id)
        if not template:
            raise ValueError(f"Email template not found with ID: {template_id}")

        if request.name != template.name and await self.repo.name_exists(request.name):
            raise ValueError(f"Email template name '{request.name}' already exists")

        template.title = request.title
        template.name = request.name
        template.subject = request.subject
        template.body = request.body
        template.cc = request.cc
        template.admin_subject = request.admin_subject
        template.admin_body = request.admin_body
        template.admin_cc = request.admin_cc
        if request.is_active is not None:
            template.is_active = request.is_active
        template.updated_by = request.updated_by

        updated_template = await self.repo.update(template)
        return EmailTemplateResponse.model_validate(updated_template)

    async def delete_email_template(self, template_id: UUID, deleted_by: UUID) -> bool:
        if not await self.repo.delete(template_id, deleted_by):
            raise ValueError(f"Email template not found with ID: {template_id}")
        return True

    async def get_email_templates_paginated(self, params: ListRequestFilters) -> dict:
        result = await self.query_handler.execute_paginated_query(
            query=select(EmailTemplate),
            model=EmailTemplate,
            params=params,
            searchable_fields=[EmailTemplate.title, EmailTemplate.name],
            sortable_fields=["created_at", "updated_at", "name"],
        )

        templates = [EmailTemplateResponse.model_validate(template) for template in result.data]

        return {"data": templates, "pagination": result.pagination}
