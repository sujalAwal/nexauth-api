from datetime import datetime, timezone
from sqlalchemy import event
from sqlalchemy.orm import Session, with_loader_criteria, ORMExecuteState
from sqlalchemy import Column, DateTime

class SoftDeleteMixin:
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)

    def soft_delete(self):
        self.deleted_at = datetime.now(timezone.utc)

    def restore(self):
        self.deleted_at = None


@event.listens_for(Session, "do_orm_execute")
def soft_delete_filter(execute_state: ORMExecuteState):
    if not execute_state.is_select:
        return

    execute_state.statement = execute_state.statement.options(
        with_loader_criteria(
            SoftDeleteMixin,
            lambda cls: cls.deleted_at.is_(None),
            include_aliases=True,
            propagate_to_loaders=True,
        )
    )