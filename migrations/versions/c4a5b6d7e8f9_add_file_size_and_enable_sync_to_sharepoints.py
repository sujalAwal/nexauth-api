"""add file_size and enable_sync to sharepoints

Revision ID: c4a5b6d7e8f9
Revises: f2a1b3c4d5e6
Create Date: 2026-08-09 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4a5b6d7e8f9'
down_revision: Union[str, Sequence[str], None] = 'f2a1b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('sharepoints', sa.Column('file_size', sa.BigInteger(), nullable=True))
    op.add_column(
        'sharepoints',
        sa.Column('enable_sync', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    )
    # Backfill file_size from the Graph item already stored in data JSONB.
    op.execute(
        "UPDATE sharepoints "
        "SET file_size = (data->>'size')::bigint "
        "WHERE data->>'size' IS NOT NULL AND file_size IS NULL;"
    )
    # Fast path for the sync candidates query (is_file + enable_sync + size order).
    op.execute(
        "CREATE INDEX IX_sharepoints_sync_candidates "
        "ON sharepoints (file_size) "
        "WHERE is_file AND enable_sync AND deleted_at IS NULL;"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX IF EXISTS IX_sharepoints_sync_candidates;")
    op.drop_column('sharepoints', 'enable_sync')
    op.drop_column('sharepoints', 'file_size')