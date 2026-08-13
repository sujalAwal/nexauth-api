"""sharepoint RAG embeddings: metadata-only chunks + department on sharepoints

Revision ID: f2a1b3c4d5e6
Revises: de8658b64750
Create Date: 2026-08-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f2a1b3c4d5e6'
down_revision: Union[str, Sequence[str], None] = 'de8658b64750'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Rename the misspelled table "sharepoints    " -> "sharepoints"
    # Use raw SQL to rename since the table name has trailing spaces
    op.execute('ALTER TABLE "sharepoints    " RENAME TO sharepoints')

    # Fix the stray index name (dropping the old, space-suffixed one).
    op.execute('DROP INDEX IF EXISTS "ix_sharepoints    _deleted_at"')
    op.create_index(op.f('ix_sharepoints_deleted_at'), 'sharepoints', ['deleted_at'], unique=False)

    # documents: sharepoint source metadata
    op.add_column('documents', sa.Column('source_type', sa.String(length=20), server_default='sharepoint', nullable=False))
    op.add_column('documents', sa.Column('uuid', sa.String(length=255), nullable=True))
    op.add_column('documents', sa.Column('url', sa.String(length=1000), nullable=True))
    op.add_column('documents', sa.Column('web_url', sa.Text(), nullable=True))
    op.add_column('documents', sa.Column('last_modified_at', sa.DateTime(timezone=True), nullable=True))

    # document_chunks: drop full text, add preview + metadata
    op.alter_column('document_chunks', 'chunk_text', existing_type=sa.Text(), nullable=True)
    op.add_column('document_chunks', sa.Column('content_preview', sa.String(length=300), nullable=True))
    op.add_column('document_chunks', sa.Column('url', sa.String(length=1000), nullable=True))
    op.add_column('document_chunks', sa.Column('content_hash', sa.String(length=64), nullable=True))
    op.add_column('document_chunks', sa.Column('chunk_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True))

    # sharepoints: department + content hash for incremental sync
    op.add_column('sharepoints', sa.Column('department', sa.String(length=100), nullable=True))
    op.add_column('sharepoints', sa.Column('content_hash', sa.String(length=64), nullable=True))

    # Re-create the HNSW vector index dropped by revision 6da6ff0cf2c8
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding_hnsw
        ON document_chunks USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX IF EXISTS idx_document_chunks_embedding_hnsw")
    op.drop_column('sharepoints', 'content_hash')
    op.drop_column('sharepoints', 'department')

    op.drop_column('document_chunks', 'chunk_metadata')
    op.drop_column('document_chunks', 'content_hash')
    op.drop_column('document_chunks', 'url')
    op.drop_column('document_chunks', 'content_preview')
    op.alter_column('document_chunks', 'chunk_text', existing_type=sa.Text(), nullable=False)

    op.drop_column('documents', 'last_modified_at')
    op.drop_column('documents', 'web_url')
    op.drop_column('documents', 'url')
    op.drop_column('documents', 'uuid')
    op.drop_column('documents', 'source_type')

    op.execute('DROP INDEX IF EXISTS ix_sharepoints_deleted_at')
    op.execute('ALTER TABLE sharepoints RENAME TO "sharepoints    "')
    op.create_index(op.f('ix_sharepoints    _deleted_at'), 'sharepoints    ', ['deleted_at'], unique=False)