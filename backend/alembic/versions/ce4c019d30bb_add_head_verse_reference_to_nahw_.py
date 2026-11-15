"""add head verse reference to nahw_annotations

Revision ID: ce4c019d30bb
Revises: ddcbc1fa1579
Create Date: 2026-10-25 23:53:25.283975

EQTB sentences may span verse boundaries, so ``head_index`` alone does not say
where the head word lives. Deployments that already hold ingested rows must run
``scripts/backfill_nahw_syntax.py`` after this migration to populate
``head_surah_number``/``head_ayah_number`` (and the corrected ``head_index``
sentinels) from the local treebank source.
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'ce4c019d30bb'
down_revision: str | None = 'ddcbc1fa1579'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('nahw_annotations', sa.Column('head_surah_number', sa.Integer(), nullable=True))
    op.add_column('nahw_annotations', sa.Column('head_ayah_number', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('nahw_annotations', 'head_ayah_number')
    op.drop_column('nahw_annotations', 'head_surah_number')
