
from pydantic import BaseModel

from app.modules.users.schemas.response.user_response import UserResponse


class UserCollection(BaseModel):
    users: list[UserResponse]