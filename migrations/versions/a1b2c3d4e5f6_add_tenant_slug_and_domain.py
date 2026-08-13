"""add tenant slug and domain

Revision ID: a1b2c3d4e5f6
Revises: 394658d4a1ce
Create Date: 2026-08-03 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "394658d4a1ce"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add slug (unique, required) and domain (optional) to tenants."""
    op.add_column("tenants", sa.Column("slug", sa.String(length=255), nullable=True))
    op.add_column("tenants", sa.Column("domain", sa.String(length=255), nullable=True))

    # Backfill slug from name for existing rows (lowercase, spaces -> hyphens)
    op.execute(
        """
        UPDATE tenants
        SET slug = trim(
            both '-' from
            regexp_replace(
                lower(regexp_replace(name, '[^a-zA-Z0-9\\s-]', '', 'g')),
                '[\\s]+',
                '-',
                'g'
            )
        )
        WHERE slug IS NULL
        """
    )
    # Fallback for names that become empty after sanitization
    op.execute(
        """
        UPDATE tenants
        SET slug = 'tenant-' || left(replace(id::text, '-', ''), 8)
        WHERE slug IS NULL OR slug = ''
        """
    )
    # Resolve any duplicate slugs by appending a short id fragment
    op.execute(
        """
        WITH ranked AS (
            SELECT id,
                   slug,
                   ROW_NUMBER() OVER (PARTITION BY lower(slug) ORDER BY created_at, id) AS rn
            FROM tenants
        )
        UPDATE tenants t
        SET slug = t.slug || '-' || left(replace(t.id::text, '-', ''), 6)
        FROM ranked r
        WHERE t.id = r.id AND r.rn > 1
        """
    )

    op.alter_column("tenants", "slug", existing_type=sa.String(length=255), nullable=False)
    op.create_index(op.f("ix_tenants_slug"), "tenants", ["slug"], unique=True)


def downgrade() -> None:
    """Remove slug and domain from tenants."""
    op.drop_index(op.f("ix_tenants_slug"), table_name="tenants")
    op.drop_column("tenants", "domain")
    op.drop_column("tenants", "slug")
