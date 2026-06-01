"""User Controller - HTTP endpoint handlers"""
from fastapi import APIRouter, Depends, status, BackgroundTasks
from sqlalchemy.orm import Session
import uuid

from app.database import get_db
from app.modules.users.schemas.requests.user_request import UserCreateRequest, UserUpdateRequest
from app.modules.users.schemas.response.user_response import UserResponse
from app.modules.users.schemas.response.user_response_collection import UserCollection
from app.modules.users.services import UserService
from app.schemas.request import ListRequestFilters
from app.schemas.response import ApiResponse
from app.core.config import settings
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema


user_router = APIRouter()

# Email configuration
email_config = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=settings.USE_CREDENTIALS,
    VALIDATE_CERTS=settings.VALIDATE_CERTS,
    TEMPLATE_FOLDER=None,
)


async def send_welcome_email(email_recipient: str, user_name: str):
    """Send welcome email to newly created user"""
    message = f"Hello {user_name},\n\nYour account has been created successfully!\n\nBest regards,\n{settings.APP_NAME} Team"
    fm = FastMail(email_config)
    
    await fm.send_message(MessageSchema(
        subject=f"User {user_name} account created successfully",
        recipients=[email_recipient],
        body=message,
        subtype="plain"
    ))


@user_router.get("/health")
def health_check():
    """Health check endpoint"""
    return {"success": True, "message": "API is healthy!"}


@user_router.get(
    '/',
    response_model=ApiResponse[UserCollection],
    status_code=status.HTTP_200_OK,
    summary="Get all users",
    description="Endpoint to retrieve a list of all users in the system"
)
def get_users(
    request: ListRequestFilters = Depends(ListRequestFilters),
    db: Session = Depends(get_db),
):
    """
    List all users with pagination, filtering, and sorting
    
    Query Parameters:
    - skip: Number of records to skip (default: 0)
    - limit: Number of records per page (default: 15)
    - search: Search by name or email
    - order_by: Field to sort by (default: updated_at)
    - sort_order: 'asc' or 'desc' (default: desc)
    """
    try:
        service = UserService(db)
        result = service.get_users_paginated(request)
        
        return ApiResponse(
            success=True,
            message="Users retrieved successfully",
            data=UserCollection(users=result["data"]),
            paginations=result["pagination"]
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message="Failed to retrieve users",
            errors={"error": str(e)}
        )


@user_router.post(
    '/',
    response_model=ApiResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    description="Endpoint to create a new user in the system"
)
def create_user(
    request: UserCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Create a new user
    
    The service validates business rules before persistence.
    Email is sent asynchronously after successful creation.
    """
    try:
        service = UserService(db)
        user_response = service.create_user(request)
        
        # Schedule email sending as background task (only after successful creation)
        background_tasks.add_task(send_welcome_email, user_response.email, user_response.name)
        
        return ApiResponse(
            success=True,
            message="User created successfully",
            data=user_response
        )
    except ValueError as e:
        # Business logic error (e.g., duplicate email)
        return ApiResponse(
            success=False,
            message=str(e),
            errors={"validation": str(e)},
            data=None
        )
    except Exception as e:
        # Unexpected error
        return ApiResponse(
            success=False,
            message="Failed to create user",
            errors={"error": str(e)},
            data=None
        )


@user_router.put(
    '/{user_id}',
    response_model=ApiResponse[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Update a user",
    description="Endpoint to update an existing user"
)
def update_user(
    user_id: uuid.UUID,
    request: UserUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Update an existing user
    
    The user_id from the URL path is used as the source of truth.
    Request body should contain the updated user data.
    """
    try:
        service = UserService(db)
        user_response = service.update_user(user_id, request)
        
        return ApiResponse(
            success=True,
            message="User updated successfully",
            data=user_response
        )
    except ValueError as e:
        # Business logic error (e.g., user not found, duplicate email)
        return ApiResponse(
            success=False,
            message=str(e),
            errors={"validation": str(e)},
            data=None
        )
    except Exception as e:
        # Unexpected error
        return ApiResponse(
            success=False,
            message="Failed to update user",
            errors={"error": str(e)},
            data=None
        )