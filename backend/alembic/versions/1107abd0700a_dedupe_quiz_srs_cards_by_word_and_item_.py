"""dedupe quiz SRS cards by word and item type

Revision ID: 1107abd0700a
Revises: 773c5ce44f99
Create Date: 2026-11-22 23:33:45.045045

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1107abd0700a"
down_revision: str | None = "773c5ce44f99"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        DELETE FROM srs_cards
        WHERE word_id IS NOT NULL
          AND deck_id IS NOT NULL
          AND id NOT IN (
              SELECT MIN(id)
              FROM srs_cards
              WHERE word_id IS NOT NULL AND deck_id IS NOT NULL
              GROUP BY user_id, deck_id, word_id, item_type
          )
        """
    )
    op.create_index('uq_srs_cards_user_deck_word_type', 'srs_cards', ['user_id', 'deck_id', 'word_id', 'item_type'], unique=True, sqlite_where=sa.text('word_id IS NOT NULL AND deck_id IS NOT NULL'), postgresql_where=sa.text('word_id IS NOT NULL AND deck_id IS NOT NULL'))


def downgrade() -> None:
    op.drop_index('uq_srs_cards_user_deck_word_type', table_name='srs_cards', sqlite_where=sa.text('word_id IS NOT NULL AND deck_id IS NOT NULL'), postgresql_where=sa.text('word_id IS NOT NULL AND deck_id IS NOT NULL'))
