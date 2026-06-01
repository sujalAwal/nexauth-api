"""Create users table

Revision ID: eb8560b5b936
Revises: 
Create Date: 2026-05-12 22:24:19.897287

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER  

# revision identifiers, used by Alembic.
revision: str = 'eb8560b5b936'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from sqlalchemy import inspect
    
    # Get the database connection
    bind = op.get_bind()
    inspector = inspect(bind)
    
    # Check if table already exists
    if 'users' not in inspector.get_table_names():
        op.create_table(
            'users',
            sa.Column('id', UNIQUEIDENTIFIER(), primary_key=True, server_default=sa.func.newid()),
            # sa.Column('id', sa.CHAR(36), primary_key=True, server_default=sa.func.newid()),
            sa.Column('name', sa.String(50), nullable=False),
            sa.Column('first_name', sa.String(50), nullable=False),
            sa.Column('middle_name', sa.String(50), nullable=True),
            sa.Column('last_name', sa.String(50), nullable=False),      
            sa.Column('email', sa.String(100), unique=True, nullable=False),
            sa.Column('password', sa.String(255), nullable=False),
            sa.Column('phone_number', sa.String(20), nullable=True),
            sa.Column('country_code', sa.String(5), nullable=False, index=True),    
            sa.Column('state', sa.String(5), nullable=True),
            sa.Column('city', sa.String(100), nullable=True),
            sa.Column('municipality', sa.String(100), nullable=True),
            sa.Column('address', sa.String(255), nullable=True), 
            sa.Column('postal_code', sa.String(10), nullable=True),
            sa.Column('is_active', sa.Boolean, nullable=False, server_default=sa.false()),
            sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()),
            sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.current_timestamp()),
            sa.Column('deleted_at', sa.DateTime, nullable=True)
        )

def downgrade() -> None:
    from sqlalchemy import inspect
    
    bind = op.get_bind()
    inspector = inspect(bind)
    
    # Check if table exists before dropping
    if 'users' in inspector.get_table_names():
        op.drop_table('users')
