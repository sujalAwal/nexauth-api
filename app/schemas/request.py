
from typing import Optional

from pydantic import BaseModel
from fastapi import Query


class ListRequestFilters:
    def __init__(
        self,
        skip: int = Query(0),
        limit: int = Query(15),
        search: Optional[str] = Query(None),
        order_by: str = Query("updated_at"),
        sort_order: str = Query("desc"),
        status: Optional[bool] = Query(None),
    ):
        self.skip = skip
        self.limit = limit
        self.search = search
        self.order_by = order_by
        self.sort_order = sort_order
        self.status = status