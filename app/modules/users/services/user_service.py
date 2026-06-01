"""User Service - Business logic layer for user operations"""
import hashlib
import secrets
from uuid import UUID
from sqlalchemy.orm import Session
from app.modules.users.models.users import User
from app.modules.users.schemas.requests.user_request import UserCreateRequest, UserUpdateRequest
from app.modules.users.schemas.response.user_response import UserResponse
from app.modules.users.repositories.user_repository import UserRepository
from app.utils.models.mixin.pagination_query_handler import PaginationQueryHandler
from app.schemas.request import ListRequestFilters
from app.schemas.pagination_response import PaginationResponse


class UserService:
    """Handles business logic for user operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = UserRepository(db)
        self.query_handler = PaginationQueryHandler()
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using PBKDF2 with SHA256.
        Returns a string in format: algorithm$salt$hash
        
        Note: Consider upgrading to bcrypt for production systems.
        To use bcrypt: pip install bcrypt
        Then use: bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        """
        salt = secrets.token_hex(32)  # 64-character hex string
        pwd_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # iterations
        ).hex()
        return f"pbkdf2_sha256${salt}${pwd_hash}"
    
    @staticmethod
    def verify_password(stored_hash: str, provided_password: str) -> bool:
        """Verify a password against its stored hash"""
        try:
            algorithm, salt, pwd_hash = stored_hash.split('$')
            provided_hash = hashlib.pbkdf2_hmac(
                'sha256',
                provided_password.encode('utf-8'),
                salt.encode('utf-8'),
                100000
            ).hex()
            return pwd_hash == provided_hash
        except (ValueError, AttributeError):
            return False
    
    def create_user(self, request: UserCreateRequest) -> UserResponse:
        """
        Create a new user with validation
        
        Raises:
            ValueError: If email already exists
        """
        # Check for duplicate email BEFORE any side effects
        if self.repo.email_exists(request.email):
            raise ValueError("Email already exists")
        
        # Hash the password
        hashed_password = self.hash_password(request.password)
        
        # Create user entity
        new_user = User(
            name=request.name,
            first_name=request.first_name,
            middle_name=request.middle_name,
            last_name=request.last_name,
            email=request.email,
            password=hashed_password,  # Store hashed password, not plaintext
            country_code=request.country,
            phone_number=request.phone_number,
            state=request.state,
            city=request.city,
            municipality=request.municipality,
            address=request.address,
            postal_code=request.postal_code
        )
        
        # Save to database
        created_user = self.repo.create(new_user)
        return UserResponse.model_validate(created_user)
    
    def update_user(self, user_id: UUID, request: UserUpdateRequest) -> UserResponse:
        """
        Update an existing user
        
        Raises:
            ValueError: If user not found or email already exists for another user
        """
        user = self.repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"User not found with ID: {user_id}")
        
        # Check if new email is being used and already exists
        if request.email != user.email:
            if self.repo.email_exists(request.email):
                raise ValueError("Email already exists")
        
        # Update fields
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
        
        updated_user = self.repo.update(user)
        return UserResponse.model_validate(updated_user)
    
    def get_users_paginated(self, params: ListRequestFilters) -> dict:
        """
        Get paginated list of users with filtering and sorting
        
        Returns:
            dict with 'data' (list of UserResponse) and 'pagination' metadata
        """
        query = self.db.query(User)
        
        # Use actual column objects for searchable fields (fixes the string issue)
        result = self.query_handler.execute_paginated_query(
            query=query,
            params=params,
            searchable_fields=[User.name, User.email],  # Use column objects, not strings
            sortable_fields=["created_at", "updated_at"]
        )
        
        # Transform to response DTOs
        users = [UserResponse.model_validate(user) for user in result["data"]]
        
        return {
            "data": users,
            "pagination": result["pagination"]
        }
    
    def get_user_by_id(self, user_id: UUID) -> UserResponse | None:
        """Get a user by ID"""
        user = self.repo.get_by_id(user_id)
        if user:
            return UserResponse.model_validate(user)
        return None
