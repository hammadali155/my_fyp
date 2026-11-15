"""add nahw relation and lookup indexes

Revision ID: ddcbc1fa1579
Revises: ab2e22cddb71
Create Date: 2026-10-24 00:06:22.579858

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'ddcbc1fa1579'
down_revision: str | None = 'ab2e22cddb71'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(op.f('ix_nahw_annotations_dep_type'), 'nahw_annotations', ['dep_type'], unique=False)
    op.create_index(op.f('ix_nahw_annotations_role'), 'nahw_annotations', ['role'], unique=False)
    op.create_index(op.f('ix_nahw_annotations_sentence_index'), 'nahw_annotations', ['sentence_index'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_nahw_annotations_sentence_index'), table_name='nahw_annotations')
    op.drop_index(op.f('ix_nahw_annotations_role'), table_name='nahw_annotations')
    op.drop_index(op.f('ix_nahw_annotations_dep_type'), table_name='nahw_annotations')
