"""add chat feedback table

Revision ID: e7d9f0a1b2c3
Revises: 625b376815aa
Create Date: 2026-08-12 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = 'e7d9f0a1b2c3'
down_revision: Union[str, Sequence[str], None] = '625b376815aa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create chat_feedbacks table for chatbot ratings (1-5) and messages."""
    op.create_table(
        'chat_feedbacks',
        sa.Column('id', UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), nullable=True),
        sa.Column('conversation_id', UUID(as_uuid=True), nullable=True),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_by', UUID(as_uuid=True), nullable=True),
        sa.CheckConstraint('rating >= 1 AND rating <= 5', name='ck_chat_feedbacks_rating'),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_chat_feedbacks_deleted_at'), 'chat_feedbacks', ['deleted_at'])


def downgrade() -> None:
    """Drop chat_feedbacks table."""
    op.drop_index(op.f('ix_chat_feedbacks_deleted_at'), table_name='chat_feedbacks')
    op.drop_table('chat_feedbacks')