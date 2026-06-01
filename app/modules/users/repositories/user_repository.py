"""User Repository - Database access layer for User operations"""
from sqlalchemy.orm import Session
from app.modules.users.models.users import User
from uuid import UUID


class UserRepository:
    """Handles all database operations for users"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, user_id: UUID) -> User | None:
        """Retrieve a user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_by_email(self, email: str) -> User | None:
        """Retrieve a user by email"""
        return self.db.query(User).filter(User.email == email).first()
    
    def email_exists(self, email: str) -> bool:
        """Check if an email already exists in the database"""
        return self.db.query(User).filter(User.email == email).first() is not None
    
    def create(self, user: User) -> User:
        """Create a new user in the database"""
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def update(self, user: User) -> User:
        """Update an existing user"""
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def get_all(self, query) -> list[User]:
        """Execute a pre-built query and return results"""
        return query.all()
    
    def count(self, query) -> int:
        """Count results from a query"""
        return query.count()
