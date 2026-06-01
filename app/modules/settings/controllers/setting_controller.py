"""Setting Controller - HTTP endpoint handlers"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app.modules.settings.schemas.requests.setting_request import (
    SettingCreateRequest,
    SettingUpdateRequest,
)
from app.modules.settings.schemas.response.setting_response import (
    SettingResponse,
    SettingCollection,
)
from app.modules.settings.services import SettingService
from app.schemas.request import ListRequestFilters
from app.schemas.response import ApiResponse

setting_router = APIRouter()


@setting_router.get(
    '/',
    response_model=ApiResponse[SettingCollection],
    status_code=status.HTTP_200_OK,
    summary="List all settings",
    description="Retrieve paginated list of settings"
)
def list_settings(
    request: ListRequestFilters = Depends(ListRequestFilters),
    db: Session = Depends(get_db),
):
    """List all settings with pagination and filtering"""
    try:
        service = SettingService(db)
        result = service.get_settings_paginated(request)
        
        return ApiResponse(
            success=True,
            message="Settings retrieved successfully",
            data=SettingCollection(settings=result["data"]),
            paginations=result["pagination"]
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message="Failed to retrieve settings",
            errors={"error": str(e)}
        )


@setting_router.get(
    '/group/{group_id}',
    response_model=ApiResponse[SettingCollection],
    status_code=status.HTTP_200_OK,
    summary="List settings by group",
    description="Retrieve all settings for a specific group"
)
def get_settings_by_group(
    group_id: UUID,
    db: Session = Depends(get_db),
):
    """Get all settings for a specific group"""
    try:
        service = SettingService(db)
        settings = service.get_settings_by_group(group_id)
        
        return ApiResponse(
            success=True,
            message="Settings retrieved successfully",
            data=SettingCollection(settings=settings)
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
            message="Failed to retrieve settings",
            errors={"error": str(e)}
        )


@setting_router.get(
    '/{setting_id}',
    response_model=ApiResponse[SettingResponse],
    status_code=status.HTTP_200_OK,
    summary="Get a setting",
    description="Retrieve a specific setting by ID"
)
def get_setting(
    setting_id: UUID,
    db: Session = Depends(get_db),
):
    """Get a specific setting"""
    try:
        service = SettingService(db)
        setting = service.get_setting_by_id(setting_id)
        
        if not setting:
            return ApiResponse(
                success=False,
                message="Setting not found",
                errors={"setting_id": f"No setting found with ID {setting_id}"}
            )
        
        return ApiResponse(
            success=True,
            message="Setting retrieved successfully",
            data=setting
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message="Failed to retrieve setting",
            errors={"error": str(e)}
        )


@setting_router.post(
    '/',
    response_model=ApiResponse[SettingResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a setting",
    description="Create a new setting"
)
def create_setting(
    request: SettingCreateRequest,
    db: Session = Depends(get_db),
):
    """Create a new setting"""
    try:
        service = SettingService(db)
        setting = service.create_setting(request)
        
        return ApiResponse(
            success=True,
            message="Setting created successfully",
            data=setting
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
            message="Failed to create setting",
            errors={"error": str(e)}
        )


@setting_router.put(
    '/{setting_id}',
    response_model=ApiResponse[SettingResponse],
    status_code=status.HTTP_200_OK,
    summary="Update a setting",
    description="Update an existing setting"
)
def update_setting(
    setting_id: UUID,
    request: SettingUpdateRequest,
    db: Session = Depends(get_db),
):
    """Update an existing setting"""
    try:
        service = SettingService(db)
        setting = service.update_setting(setting_id, request)
        
        return ApiResponse(
            success=True,
            message="Setting updated successfully",
            data=setting
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
            message="Failed to update setting",
            errors={"error": str(e)}
        )


@setting_router.delete(
    '/{setting_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a setting",
    description="Delete a setting (soft delete)"
)
def delete_setting(
    setting_id: UUID,
    db: Session = Depends(get_db),
):
    """Delete a setting"""
    try:
        service = SettingService(db)
        service.delete_setting(setting_id)
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
            message="Failed to delete setting",
            errors={"error": str(e)}
        )
