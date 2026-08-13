from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.modules.department.schemas.requests.department_request import (
    DepartmentCreateRequest,
    DepartmentUpdateRequest,
)
from app.modules.department.schemas.response.department_response import (
    DepartmentCollection,
    DepartmentResponse,
)
from app.modules.department.services import DepartmentService
from app.schemas.request import ListRequestFilters
from app.schemas.response import ApiResponse


department_router = APIRouter()


@department_router.get("", response_model=ApiResponse[DepartmentCollection])
async def list_departments(
    request: ListRequestFilters = Depends(ListRequestFilters),
    db: AsyncSession = Depends(get_db),
):
    try:
        service = DepartmentService(db)
        result = await service.get_departments_paginated(request)

        return ApiResponse(
            success=True,
            message="Departments retrieved successfully",
            data=DepartmentCollection(data=result["data"]),
            paginations=result["pagination"],
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@department_router.get("/{department_id}", response_model=ApiResponse[DepartmentResponse])
async def get_department(
    department_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    try:
        service = DepartmentService(db)
        department = await service.get_department_by_id(department_id)

        if not department:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

        return ApiResponse(
            success=True,
            message="Department retrieved successfully",
            data=department,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@department_router.post("", response_model=ApiResponse[DepartmentResponse], status_code=status.HTTP_201_CREATED)
async def create_department(
    request: DepartmentCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        service = DepartmentService(db)
        department = await service.create_department(request=request, created_by=UUID(int=0))

        return ApiResponse(
            success=True,
            message="Department created successfully",
            data=department,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@department_router.put("/{department_id}", response_model=ApiResponse[DepartmentResponse])
async def update_department(
    department_id: UUID,
    request: DepartmentUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        service = DepartmentService(db)
        department = await service.update_department(
            department_id=department_id,
            request=request,
            updated_by=UUID(int=0),
        )

        return ApiResponse(
            success=True,
            message="Department updated successfully",
            data=department,
        )
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@department_router.delete("/{department_id}", response_model=ApiResponse[DepartmentResponse])
async def delete_department(
    department_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    try:
        service = DepartmentService(db)
        department = await service.delete_department(department_id=department_id, deleted_by=UUID(int=0))

        return ApiResponse(
            success=True,
            message="Department deleted successfully",
            data=department,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@department_router.get("/active/list", response_model=ApiResponse[DepartmentCollection])
async def list_active_departments(
    db: AsyncSession = Depends(get_db),
):
    try:
        service = DepartmentService(db)
        result = await service.list_active_departments()

        return ApiResponse(
            success=True,
            message="Active departments retrieved successfully",
            data=DepartmentCollection(data=result),
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))