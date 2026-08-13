"""User Service - Business logic layer for user operations"""
import hashlib
import secrets
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.users.models.users import User
from app.modules.users.schemas.requests.user_request import UserCreateRequest, UserUpdateRequest
from app.modules.users.schemas.response.user_response import UserResponse
from app.modules.users.repositories.user_repository import UserRepository
from app.utils.models.mixin.pagination_query_handler import PaginationQueryHandler
from app.schemas.request import ListRequestFilters


class UserService:
    """Handles business logic for user operations"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = UserRepository(db)
        self.query_handler = PaginationQueryHandler(db)

    @staticmethod
    def hash_password(password: str) -> str:
        salt = secrets.token_hex(32)
        pwd_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            100000,
        ).hex()
        return f"pbkdf2_sha256${salt}${pwd_hash}"

    @staticmethod
    def verify_password(stored_hash: str, provided_password: str) -> bool:
        try:
            algorithm, salt, pwd_hash = stored_hash.split("$")
            provided_hash = hashlib.pbkdf2_hmac(
                "sha256",
                provided_password.encode("utf-8"),
                salt.encode("utf-8"),
                100000,
            ).hex()
            return pwd_hash == provided_hash
        except (ValueError, AttributeError):
            return False

    async def create_user(self, request: UserCreateRequest) -> UserResponse:
        if await self.repo.email_exists(request.email):
            raise ValueError("Email already exists")

        hashed_password = self.hash_password(request.password)

        new_user = User(
            name=request.name,
            first_name=request.first_name,
            middle_name=request.middle_name,
            last_name=request.last_name,
            email=request.email,
            password=hashed_password,
            country_code=request.country,
            phone_number=request.phone_number,
            state=request.state,
            city=request.city,
            municipality=request.municipality,
            address=request.address,
            postal_code=request.postal_code,
        )

        created_user = await self.repo.create(new_user)
        return UserResponse.model_validate(created_user)

    async def update_user(self, user_id: UUID, request: UserUpdateRequest) -> UserResponse:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"User not found with ID: {user_id}")

        if request.email != user.email:
            if await self.repo.email_exists(request.email):
                raise ValueError("Email already exists")

        user.name = request.name
        user.first_name = request.first_name
        user.middle_name = request.middle_name
        user.last_name = request.last_name
        user.email = request.email
        user.country_code = request.country
        user.phone_number = request.phone_number
        user.state = request.state
        user.city = request.city
        user.municipality = request.municipality
        user.address = request.address
        user.postal_code = request.postal_code

        updated_user = await self.repo.update(user)
        return UserResponse.model_validate(updated_user)

    async def get_users_paginated(self, params: ListRequestFilters) -> dict:
        result = await self.query_handler.execute_paginated_query(
            query=select(User),
            model=User,
            params=params,
            searchable_fields=[User.name, User.email],
            sortable_fields=["created_at", "updated_at"],
        )

        users = [UserResponse.model_validate(user) for user in result.data]

        return {"data": users, "pagination": result.pagination}

    async def get_user_by_id(self, user_id: UUID) -> UserResponse | None:
        user = await self.repo.get_by_id(user_id)
        if user:
            return UserResponse.model_validate(user)
        return None
