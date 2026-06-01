"""Add email_verified_at to users table

Revision ID: 001add_email_verified
Revises: eb8560b5b936
Create Date: 2026-05-21 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001add_email_verified'
down_revision: Union[str, Sequence[str], None] = 'eb8560b5b936'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from sqlalchemy import inspect

    bind = op.get_bind()
    inspector = inspect(bind)

    # Check if column doesn't exist before adding
    if 'users' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('users')]
        if 'email_verified_at' not in columns:
            op.add_column('users', sa.Column('email_verified_at', sa.DateTime, nullable=True))


def downgrade() -> None:
    from sqlalchemy import inspect

    bind = op.get_bind()
    inspector = inspect(bind)

    # Check if column exists before dropping
    if 'users' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('users')]
        if 'email_verified_at' in columns:
            op.drop_column('users', 'email_verified_at')
