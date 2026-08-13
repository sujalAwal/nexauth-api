from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.database import get_db
from app.modules.public.settings.services.setting_public_service import SettingPublicService
from app.modules.public.settings.schemas.response.setting_public_response import SettingPublicResponse, SettingPublicCollection
from app.schemas.response import ApiResponse

setting_public_router = APIRouter()


@setting_public_router.get("/", response_model=ApiResponse[SettingPublicCollection])
async def list_settings(db: AsyncSession = Depends(get_db)):
    """Get all active settings (public endpoint)."""
    try:
        service = SettingPublicService(db)
        settings = await service.get_all_active_settings()

        return ApiResponse(
            success=True,
            message="Settings retrieved successfully",
            data=SettingPublicCollection(data=[SettingPublicResponse.model_validate(s) for s in settings]),
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@setting_public_router.get("/group/{group_id}", response_model=ApiResponse[SettingPublicCollection])
async def get_settings_by_group(group_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get settings by group (public endpoint)."""
    try:
        service = SettingPublicService(db)
        settings = await service.get_settings_by_group(group_id)

        return ApiResponse(
            success=True,
            message="Group settings retrieved successfully",
            data=SettingPublicCollection(data=[SettingPublicResponse.model_validate(s) for s in settings]),
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@setting_public_router.get("/{name}", response_model=ApiResponse[SettingPublicResponse])
async def get_setting_by_name(name: str, db: AsyncSession = Depends(get_db)):
    """Get setting by name (public endpoint)."""
    try:
        service = SettingPublicService(db)
        setting = await service.get_setting_by_name(name)

        if not setting:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Setting not found")

        return ApiResponse(
            success=True,
            message="Setting retrieved successfully",
            data=SettingPublicResponse.model_validate(setting),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
