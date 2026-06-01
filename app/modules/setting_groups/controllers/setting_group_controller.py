"""SettingGroup Controller - HTTP endpoint handlers"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from uuid import UUID
import json

from app.database import get_db
from app.modules.setting_groups.schemas.requests.setting_group_request import (
    SettingGroupCreateRequest,
    SettingGroupUpdateRequest,
)
from app.modules.setting_groups.schemas.response.setting_group_response import (
    SettingGroupResponse,
    SettingGroupCollection,
)
from app.modules.setting_groups.services import SettingGroupService
from app.schemas.request import ListRequestFilters
from app.schemas.response import ApiResponse

setting_group_router = APIRouter()


@setting_group_router.get(
    '/',
    response_model=ApiResponse[SettingGroupCollection],
    status_code=status.HTTP_200_OK,
    summary="List all setting groups",
    description="Retrieve paginated list of setting groups"
)
def list_setting_groups(
    request: ListRequestFilters = Depends(ListRequestFilters),
    db: Session = Depends(get_db),
):
    """List all setting groups with pagination and filtering"""
    try:
        service = SettingGroupService(db)
        result = service.get_setting_groups_paginated(request)
        
        return ApiResponse(
            success=True,
            message="Setting groups retrieved successfully",
            data=SettingGroupCollection(groups=result["data"]),
            paginations=result["pagination"]
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message="Failed to retrieve setting groups",
            errors={"error": str(e)}
        )


@setting_group_router.get(
    '/{group_id}',
    response_model=ApiResponse[SettingGroupResponse],
    status_code=status.HTTP_200_OK,
    summary="Get a setting group",
    description="Retrieve a specific setting group by ID"
)
def get_setting_group(
    group_id: UUID,
    db: Session = Depends(get_db),
):
    """Get a specific setting group"""
    try:
        service = SettingGroupService(db)
        group = service.get_setting_group_by_id(group_id)
        
        if not group:
            return ApiResponse(
                success=False,
                message="Setting group not found",
                errors={"group_id": f"No group found with ID {group_id}"}
            )
        
        return ApiResponse(
            success=True,
            message="Setting group retrieved successfully",
            data=group
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message="Failed to retrieve setting group",
            errors={"error": str(e)}
        )


@setting_group_router.post(
    '/',
    response_model=ApiResponse[SettingGroupResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a setting group",
    description="Create a new setting group"
)
def create_setting_group(
    request: SettingGroupCreateRequest,
    db: Session = Depends(get_db),
):
    """Create a new setting group"""
    try:
        service = SettingGroupService(db)
        group = service.create_setting_group(request)
        
        return ApiResponse(
            success=True,
            message="Setting group created successfully",
            data=group
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
            message="Failed to create setting group",
            errors={"error": str(e)}
        )


@setting_group_router.put(
    '/{group_id}',
    response_model=ApiResponse[SettingGroupResponse],
    status_code=status.HTTP_200_OK,
    summary="Update a setting group",
    description="Update an existing setting group"
)
def update_setting_group(
    group_id: UUID,
    request: SettingGroupUpdateRequest,
    db: Session = Depends(get_db),
):
    """Update an existing setting group"""
    try:
        service = SettingGroupService(db)
        group = service.update_setting_group(group_id, request)
        
        return ApiResponse(
            success=True,
            message="Setting group updated successfully",
            data=group
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
            message="Failed to update setting group",
            errors={"error": str(e)}
        )


@setting_group_router.delete(
    '/{group_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a setting group",
    description="Delete a setting group (soft delete)"
)
def delete_setting_group(
    group_id: UUID,
    db: Session = Depends(get_db),
):
    """Delete a setting group"""
    try:
        service = SettingGroupService(db)
        service.delete_setting_group(group_id)
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
            message="Failed to delete setting group",
            errors={"error": str(e)}
        )
