"""EmailTemplate Service - Business logic layer"""
from uuid import UUID
from sqlalchemy.orm import Session
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
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = EmailTemplateRepository(db)
        self.query_handler = PaginationQueryHandler()
    
    def create_email_template(self, request: EmailTemplateCreateRequest) -> EmailTemplateResponse:
        """Create a new email template"""
        # Validate unique name
        if self.repo.name_exists(request.name):
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
        
        created_template = self.repo.create(new_template)
        return EmailTemplateResponse.model_validate(created_template)
    
    def get_email_template_by_id(self, template_id: UUID) -> EmailTemplateResponse | None:
        """Retrieve an email template by ID"""
        template = self.repo.get_by_id(template_id)
        if template:
            return EmailTemplateResponse.model_validate(template)
        return None
    
    def get_email_template_by_name(self, name: str) -> EmailTemplateResponse | None:
        """Retrieve an email template by name"""
        template = self.repo.get_by_name(name)
        if template:
            return EmailTemplateResponse.model_validate(template)
        return None
    
    def update_email_template(self, template_id: UUID, request: EmailTemplateUpdateRequest) -> EmailTemplateResponse:
        """Update an existing email template"""
        template = self.repo.get_by_id(template_id)
        if not template:
            raise ValueError(f"Email template not found with ID: {template_id}")
        
        # Check if new name is unique
        if request.name != template.name and self.repo.name_exists(request.name):
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
        
        updated_template = self.repo.update(template)
        return EmailTemplateResponse.model_validate(updated_template)
    
    def delete_email_template(self, template_id: UUID, deleted_by: UUID) -> bool:
        """Delete (soft delete) an email template"""
        if not self.repo.delete(template_id, deleted_by):
            raise ValueError(f"Email template not found with ID: {template_id}")
        return True
    
    def get_email_templates_paginated(self, params: ListRequestFilters) -> dict:
        """Get paginated list of email templates"""
        query = self.db.query(EmailTemplate)
        
        result = self.query_handler.execute_paginated_query(
            query=query,
            params=params,
            searchable_fields=[EmailTemplate.title, EmailTemplate.name],
            sortable_fields=["created_at", "updated_at", "name"]
        )
        
        templates = [EmailTemplateResponse.model_validate(template) for template in result["data"]]
        
        return {
            "data": templates,
            "pagination": result["pagination"]
        }
