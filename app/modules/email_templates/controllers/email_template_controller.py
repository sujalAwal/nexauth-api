"""EmailTemplate Controller - HTTP endpoint handlers"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.database import get_db
from app.modules.email_templates.schemas.requests.email_template_request import (
    EmailTemplateCreateRequest,
    EmailTemplateUpdateRequest,
)
from app.modules.email_templates.schemas.response.email_template_response import (
    EmailTemplateResponse,
    EmailTemplateCollection,
)
from app.modules.email_templates.services import EmailTemplateService
from app.schemas.request import ListRequestFilters
from app.schemas.response import ApiResponse

email_template_router = APIRouter()


@email_template_router.get(
    '/',
    response_model=ApiResponse[EmailTemplateCollection],
    status_code=status.HTTP_200_OK,
    summary="List all email templates",
    description="Retrieve paginated list of email templates"
)
async def list_email_templates(
    request: ListRequestFilters = Depends(ListRequestFilters),
    db: AsyncSession = Depends(get_db),
):
    """List all email templates with pagination and filtering"""
    try:
        service = EmailTemplateService(db)
        result = await service.get_email_templates_paginated(request)
        
        return ApiResponse(
            success=True,
            message="Email templates retrieved successfully",
            data=EmailTemplateCollection(templates=result["data"]),
            paginations=result["pagination"]
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message="Failed to retrieve email templates",
            errors={"error": str(e)}
        )


@email_template_router.get(
    '/{template_id}',
    response_model=ApiResponse[EmailTemplateResponse],
    status_code=status.HTTP_200_OK,
    summary="Get an email template",
    description="Retrieve a specific email template by ID"
)
async def get_email_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific email template"""
    try:
        service = EmailTemplateService(db)
        template = await service.get_email_template_by_id(template_id)
        
        if not template:
            return ApiResponse(
                success=False,
                message="Email template not found",
                errors={"template_id": f"No template found with ID {template_id}"}
            )
        
        return ApiResponse(
            success=True,
            message="Email template retrieved successfully",
            data=template
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message="Failed to retrieve email template",
            errors={"error": str(e)}
        )


@email_template_router.get(
    '/by-name/{name}',
    response_model=ApiResponse[EmailTemplateResponse],
    status_code=status.HTTP_200_OK,
    summary="Get email template by name",
    description="Retrieve a specific email template by name"
)
async def get_email_template_by_name(
    name: str,
    db: AsyncSession = Depends(get_db),
):
    """Get an email template by name"""
    try:
        service = EmailTemplateService(db)
        template = await service.get_email_template_by_name(name)
        
        if not template:
            return ApiResponse(
                success=False,
                message="Email template not found",
                errors={"name": f"No template found with name '{name}'"}
            )
        
        return ApiResponse(
            success=True,
            message="Email template retrieved successfully",
            data=template
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message="Failed to retrieve email template",
            errors={"error": str(e)}
        )


@email_template_router.post(
    '/',
    response_model=ApiResponse[EmailTemplateResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create an email template",
    description="Create a new email template"
)
async def create_email_template(
    request: EmailTemplateCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new email template"""
    try:
        service = EmailTemplateService(db)
        template = await service.create_email_template(request)
        
        return ApiResponse(
            success=True,
            message="Email template created successfully",
            data=template
        )
    except ValueError as e:
        return ApiResponse(
            success=False,
            message=str(e),
            errors={"validation": str(e)}
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message="Failed to create email template",
            errors={"error": str(e)}
        )


@email_template_router.put(
    '/{template_id}',
    response_model=ApiResponse[EmailTemplateResponse],
    status_code=status.HTTP_200_OK,
    summary="Update an email template",
    description="Update an existing email template"
)
async def update_email_template(
    template_id: UUID,
    request: EmailTemplateUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Update an existing email template"""
    try:
        service = EmailTemplateService(db)
        template = await service.update_email_template(template_id, request)
        
        return ApiResponse(
            success=True,
            message="Email template updated successfully",
            data=template
        )
    except ValueError as e:
        return ApiResponse(
            success=False,
            message=str(e),
            errors={"validation": str(e)}
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message="Failed to update email template",
            errors={"error": str(e)}
        )


@email_template_router.delete(
    '/{template_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an email template",
    description="Delete an email template (soft delete)"
)
async def delete_email_template(
    template_id: UUID,
    deleted_by: UUID = Depends(lambda: UUID(int=0)),  # Should come from authenticated user
    db: AsyncSession = Depends(get_db),
):
    """Delete an email template"""
    try:
        service = EmailTemplateService(db)
        await service.delete_email_template(template_id, deleted_by)
        return None
    except ValueError as e:
        return ApiResponse(
            success=False,
            message=str(e),
            errors={"validation": str(e)}
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message="Failed to delete email template",
            errors={"error": str(e)}
        )
