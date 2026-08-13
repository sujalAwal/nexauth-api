from alembic.environment import Any
from pydantic import BaseModel
from typing import List, Generic, TypeVar

T = TypeVar('T')

class PaginationResponse(BaseModel):
       skip: int
       limit: int
       total: int
       page: int
       has_more: bool
       total_pages: int

class PaginatedCollectionResponse(BaseModel, Generic[T]):
    data: List[T]
    pagination: PaginationResponse