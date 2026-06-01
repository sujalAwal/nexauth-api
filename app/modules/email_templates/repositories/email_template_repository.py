"""EmailTemplate Repository - Database access layer"""
from sqlalchemy.orm import Session
from uuid import UUID
from app.modules.email_templates.models.email_template import EmailTemplate


class EmailTemplateRepository:
    """Handles all database operations for email templates"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, template_id: UUID) -> EmailTemplate | None:
        """Retrieve an email template by ID"""
        return self.db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
    
    def get_by_name(self, name: str) -> EmailTemplate | None:
        """Retrieve an email template by name"""
        return self.db.query(EmailTemplate).filter(EmailTemplate.name == name).first()
    
    def name_exists(self, name: str) -> bool:
        """Check if a template name already exists"""
        return self.db.query(EmailTemplate).filter(EmailTemplate.name == name).exists().scalar()
    
    def get_all_active(self) -> list[EmailTemplate]:
        """Retrieve all active email templates"""
        return self.db.query(EmailTemplate).filter(EmailTemplate.is_active == True).all()
    
    def create(self, template: EmailTemplate) -> EmailTemplate:
        """Create a new email template"""
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template
    
    def update(self, template: EmailTemplate) -> EmailTemplate:
        """Update an existing email template"""
        self.db.commit()
        self.db.refresh(template)
        return template
    
    def delete(self, template_id: UUID, deleted_by: UUID) -> bool:
        """Soft delete an email template"""
        template = self.get_by_id(template_id)
        if template:
            template.deleted_at = datetime.now(timezone.utc)
            template.deleted_by = deleted_by
            self.db.commit()
            return True
        return False
