# Global filter - Automatically hide soft deleted records
from sqlalchemy import event
from sqlalchemy.orm import ORMExecuteState, with_loader_criteria, Session

from app.utils.models.mixin.soft_delete import SoftDeleteMixin


@event.listens_for(Session, "do_orm_execute")
def _soft_delete_filter(execute_state: ORMExecuteState):
    """Automatically apply soft delete filter on all SELECT queries"""
    
    if not execute_state.is_select:
        return

    # Skip if it's a relationship load or column load (optional optimization)
    if execute_state.is_relationship_load or execute_state.is_column_load:
        return

    execute_state.statement = execute_state.statement.options(
        with_loader_criteria(
            SoftDeleteMixin,
            lambda cls: cls.deleted_at.is_(None),
            include_aliases=True,
            propagate_to_loaders=True   # Important for relationships
        )
    )