"""add sentence_index to nahw_annotations

Revision ID: ab2e22cddb71
Revises: ad73c2a620ae
Create Date: 2026-10-21 14:48:47.384796

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'ab2e22cddb71'
down_revision: str | None = 'ad73c2a620ae'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('nahw_annotations', sa.Column('sentence_index', sa.Integer(), nullable=True))
    op.create_index(
        'ix_nahw_annotations_verse_sentence',
        'nahw_annotations',
        ['verse_id', 'sentence_index'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index('ix_nahw_annotations_verse_sentence', table_name='nahw_annotations')
    op.drop_column('nahw_annotations', 'sentence_index')
