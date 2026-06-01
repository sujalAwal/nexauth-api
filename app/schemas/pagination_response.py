from alembic.environment import Any
from pydantic import BaseModel


class PaginationResponse(BaseModel):
       skip: int
       limit: int
       total: int
       page: int
       has_more: bool
       total_pages: int