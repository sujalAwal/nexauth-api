"""
Global soft-delete filter — automatically excludes soft-deleted records from
all SELECT queries across the entire application.

This is the SINGLE canonical listener. The SoftDeleteMixin class (which adds
the `deleted_at` column) lives in app/utils/models/mixin/soft_delete.py but
intentionally does NOT register any event — all listener logic lives here.

To bypass the filter for a specific query (e.g. restore endpoints), pass:
    execution_options={"include_deleted": True}
"""
from sqlalchemy import event
from sqlalchemy.orm import ORMExecuteState, with_loader_criteria, Session

from app.utils.models.mixin.soft_delete import SoftDeleteMixin


@event.listens_for(Session, "do_orm_execute")
def _soft_delete_filter(execute_state: ORMExecuteState):
    """Automatically apply soft-delete filter on all SELECT queries."""

    # Only intercept SELECT statements
    if not execute_state.is_select:
        return

    # Skip sub-loads (relationship / column loads) — they inherit the criteria
    # from the parent query already via propagate_to_loaders=True, so applying
    # it here again would double the work.
    if execute_state.is_relationship_load or execute_state.is_column_load:
        return

    # Allow explicit bypass (e.g. restore queries, admin soft-delete lookups)
    if execute_state.execution_options.get("include_deleted", False):
        return

    execute_state.statement = execute_state.statement.options(
        with_loader_criteria(
            SoftDeleteMixin,
            lambda cls: cls.deleted_at.is_(None),
            include_aliases=True,
            propagate_to_loaders=True,   # automatically covers eager-loaded relationships
        )
    )