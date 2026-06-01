from pprint import pprint

from app.schemas.pagination_response import PaginationResponse
class PaginationQueryHandler:
    """
    Handles database queries with pagination, filtering, and sorting.
    Applies all filters at DATABASE level, not in-memory.
    """

    def filter_by_search(self, query, search_query, searchable_fields):
        """Apply search filter to SQLAlchemy query"""
        if search_query:
            search_filter = None
            for field in searchable_fields:
                if search_filter is None:
                    search_filter = field.ilike(f"%{search_query}%")
                else:
                    search_filter = search_filter | field.ilike(f"%{search_query}%")
            query = query.filter(search_filter)
        return query

    def apply_sorting(self, query, order_by, sort_order, sortable_fields):
        """Apply sorting to SQLAlchemy query"""
        pprint(query.__dict__)
        if order_by in sortable_fields:
            model = query.column_descriptions[0]['entity']
            order_field = getattr(model, order_by)
            if sort_order == "asc":
                query = query.order_by(order_field.asc())
            else:
                query = query.order_by(order_field.desc())
        return query

    def apply_pagination(self, query, skip, limit):
        """Apply pagination to SQLAlchemy query"""
        return query.offset(skip).limit(limit)

    def get_count_before_pagination(self, query):
        """Get total count BEFORE pagination"""
        return query.count()

    def build_pagination_metadata(self, total, skip, limit) -> PaginationResponse:
        """Calculate pagination metadata"""
        page = (skip // limit) + 1
        has_more = (skip + limit) < total
        return PaginationResponse(
            skip=skip,
            limit=limit,
            total=total,
            page=page,
            has_more=has_more,
            total_pages=(total + limit - 1) // limit  # Ceiling division
        )

    def execute_paginated_query(self, query, params, searchable_fields, sortable_fields):
        """
        Execute complete paginated query with filters and sorting.
        
        Steps:
        1. Filter by search
        2. Get total count
        3. Apply sorting
        4. Apply pagination
        5. Execute query (fetch only needed rows)
        6. Build metadata
        """
        # Apply search filter
        query = self.filter_by_search(query, params.search, searchable_fields)
        
        # Get total BEFORE pagination
        total = self.get_count_before_pagination(query)
        
        # Apply sorting
        query = self.apply_sorting(query, params.order_by, params.sort_order, sortable_fields)
        
        # Apply pagination
        query = self.apply_pagination(query, params.skip, params.limit)
        
        # Execute query and fetch results
        items = query.all()
        
        # Build metadata
        pagination = self.build_pagination_metadata(total, params.skip, params.limit)
        
        return {
            "data": items,
            "pagination": pagination
        }


# ============================================================================
# USAGE IN SERVICES
# ============================================================================

'''
from sqlalchemy.orm import Session
from models import User

class UserService:
    """Service for User operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.query_handler = PaginationQueryHandler()
    
    def get_users_list(self, params: CommonQueryParams):
        """Get list of users with filtering, sorting, pagination"""
        query = self.db.query(User)
        
        return self.query_handler.execute_paginated_query(
            query=query,
            params=params,
            searchable_fields=[User.name, User.email],
            sortable_fields=["created_at", "name", "email"]
        )
'''