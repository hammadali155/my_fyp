from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.srs import SRSCard


class Deck(TimestampMixin, Base):
    __tablename__ = "decks"
    __table_args__ = (Index("ix_decks_user", "user_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    cards: Mapped[list[SRSCard]] = relationship("SRSCard", back_populates="deck", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Deck id={self.id} user={self.user_id} name={self.name!r}>"
