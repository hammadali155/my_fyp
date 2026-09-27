from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class SRSCard(TimestampMixin, Base):
    __tablename__ = "srs_cards"
    __table_args__ = (
        Index("ix_srs_cards_user_due", "user_id", "due_date"),
        Index("ix_srs_cards_user_state", "user_id", "state"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    word_id: Mapped[int | None] = mapped_column(
        ForeignKey("words.id", ondelete="SET NULL"), nullable=True, index=True
    )

    item_type: Mapped[str] = mapped_column(
        String(30), nullable=False, default="root"
    )  # root, vocabulary, verse_fill_blank, grammar_rule
    front: Mapped[str] = mapped_column(Text, nullable=False)
    back: Mapped[str] = mapped_column(Text, nullable=False)
    hint: Mapped[str | None] = mapped_column(Text, nullable=True)

    surah_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ayah_number: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # SM-2 Scheduling Parameters
    state: Mapped[str] = mapped_column(
        String(20), nullable=False, default="new"
    )  # new, learning, review, graduated
    ease_factor: Mapped[float] = mapped_column(Float, nullable=False, default=2.50)
    interval_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    repetitions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    lapses: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    due_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    last_reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    review_logs: Mapped[list[SRSReviewLog]] = relationship(
        back_populates="card", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<SRSCard id={self.id} user_id={self.user_id} state={self.state!r} due={self.due_date}>"


class SRSReviewLog(TimestampMixin, Base):
    __tablename__ = "srs_review_logs"
    __table_args__ = (Index("ix_srs_logs_user_reviewed", "user_id", "reviewed_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    card_id: Mapped[int] = mapped_column(
        ForeignKey("srs_cards.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1=Again, 2=Hard, 3=Good, 4=Easy
    review_duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    previous_interval_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    new_interval_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    previous_ease_factor: Mapped[float] = mapped_column(Float, nullable=False, default=2.50)
    new_ease_factor: Mapped[float] = mapped_column(Float, nullable=False, default=2.50)

    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    card: Mapped[SRSCard] = relationship(back_populates="review_logs")

    def __repr__(self) -> str:
        return f"<SRSReviewLog id={self.id} card_id={self.card_id} rating={self.rating}>"
