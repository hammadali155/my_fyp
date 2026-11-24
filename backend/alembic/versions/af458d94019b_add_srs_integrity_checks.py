"""add srs integrity checks

Revision ID: af458d94019b
Revises: b7224c79c2f2
Create Date: 2026-11-24 00:45:33.918672

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "af458d94019b"
down_revision: str | None = "b7224c79c2f2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table(
        "srs_cards",
        recreate="always",
        table_args=(
            sa.CheckConstraint(
                "state IN ('new', 'learning', 'review', 'graduated')",
                name="ck_srs_cards_state",
            ),
        ),
    ):
        pass

    with op.batch_alter_table(
        "srs_review_logs",
        recreate="always",
        table_args=(
            sa.CheckConstraint("rating BETWEEN 1 AND 4", name="ck_srs_review_logs_rating"),
        ),
    ):
        pass


def downgrade() -> None:
    with op.batch_alter_table(
        "srs_review_logs",
        recreate="always",
        table_args=(),
    ):
        pass

    with op.batch_alter_table(
        "srs_cards",
        recreate="always",
        table_args=(),
    ):
        pass
