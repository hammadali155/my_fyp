from __future__ import annotations

from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.deck import Deck
from app.models.quran import Surah, Verse, Word
from app.models.srs import SRSCard
from app.schemas.deck import DeckCreate, DeckResponse, DeckStateCounts

logger = get_logger("services.deck")

STATES = ("new", "learning", "review", "graduated")


class DeckService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_decks(self, user_id: int) -> list[DeckResponse]:
        decks = (
            await self.db.execute(
                select(Deck).where(Deck.user_id == user_id).order_by(Deck.created_at.asc())
            )
        ).scalars().all()
        out: list[DeckResponse] = []
        for deck in decks:
            counts = await self._state_counts(user_id, deck.id)
            out.append(self._to_response(deck, counts))
        return out

    async def create_deck(self, user_id: int, req: DeckCreate) -> DeckResponse:
        deck = Deck(user_id=user_id, name=req.name.strip(), is_default=False)
        self.db.add(deck)
        await self.db.commit()
        await self.db.refresh(deck)

        from app.services.progress_service import ProgressService

        await ProgressService(self.db).check_and_award_badges(user_id)
        await self.db.commit()
        return self._to_response(deck, DeckStateCounts())

    async def get_deck(self, user_id: int, deck_id: int) -> Deck:
        deck = (
            await self.db.execute(
                select(Deck).where(Deck.id == deck_id, Deck.user_id == user_id)
            )
        ).scalar_one_or_none()
        if deck is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deck not found")
        return deck

    async def add_words(self, user_id: int, deck_id: int, word_ids: list[int]) -> tuple[int, int, list[int]]:
        deck = await self.get_deck(user_id, deck_id)
        added = 0
        skipped = 0
        card_ids: list[int] = []
        for word_id in word_ids:
            dup = await self.db.execute(
                select(SRSCard.id).where(
                    SRSCard.user_id == user_id, SRSCard.deck_id == deck.id, SRSCard.word_id == word_id
                )
            )
            if dup.scalar_one_or_none() is not None:
                skipped += 1
                continue
            word = (await self.db.execute(select(Word).where(Word.id == word_id))).scalar_one_or_none()
            if word is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Word {word_id} not found")
            verse = (await self.db.execute(select(Verse).where(Verse.id == word.verse_id))).scalar_one_or_none()
            surah_number: int | None = None
            if verse is not None:
                surah = (await self.db.execute(select(Surah).where(Surah.id == verse.surah_id))).scalar_one_or_none()
                surah_number = surah.number if surah else None
            card = SRSCard(
                user_id=user_id,
                word_id=word.id,
                deck_id=deck.id,
                item_type="vocabulary",
                front=word.text_uthmani,
                back=word.translation_en or "",
                hint=word.root,
                surah_number=surah_number,
                ayah_number=verse.ayah_number if verse else None,
                due_date=datetime.now(UTC),
            )
            self.db.add(card)
            await self.db.flush()
            card_ids.append(card.id)
            added += 1
        await self.db.commit()
        return added, skipped, card_ids

    async def delete_deck(self, user_id: int, deck_id: int) -> None:
        deck = await self.get_deck(user_id, deck_id)
        await self.db.delete(deck)
        await self.db.commit()

    async def _state_counts(self, user_id: int, deck_id: int) -> DeckStateCounts:
        rows = (
            await self.db.execute(
                select(SRSCard.state, func.count(SRSCard.id))
                .where(SRSCard.user_id == user_id, SRSCard.deck_id == deck_id)
                .group_by(SRSCard.state)
            )
        ).all()
        counts = DeckStateCounts()
        for state, count in rows:
            if state in STATES:
                setattr(counts, state, count)
        return counts

    def _to_response(self, deck: Deck, counts: DeckStateCounts) -> DeckResponse:
        total = counts.new + counts.learning + counts.review + counts.graduated
        return DeckResponse(
            id=deck.id,
            name=deck.name,
            is_default=deck.is_default,
            created_at=deck.created_at,
            updated_at=deck.updated_at,
            counts=counts,
            total_cards=total,
        )
