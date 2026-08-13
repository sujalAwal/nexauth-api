from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import DateTime


class SoftDeleteMixin:
    """
    Mixin that adds soft-delete support to any SQLAlchemy model.

    Adds a `deleted_at` column (timezone-aware). Records with a non-null
    `deleted_at` are treated as deleted and automatically excluded from
    SELECT queries via the global event listener in app/utils/soft_delete.py.
    """
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,     # indexed so the WHERE deleted_at IS NULL filter is fast
        default=None,
    )

    def soft_delete(self):
        """Mark this record as deleted (sets deleted_at to now)."""
        self.deleted_at = datetime.now(timezone.utc)

    def restore(self):
        """Undelete this record (clears deleted_at)."""
        self.deleted_at = None