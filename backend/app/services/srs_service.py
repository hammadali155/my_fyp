from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.quran import Surah, Verse, Word
from app.models.srs import SRSCard, SRSReviewLog
from app.models.user import User
from app.schemas.srs import (
    SRSCardCreate,
    SRSCardResponse,
    SRSDueQueueResponse,
    SRSReviewResponse,
    SRSStatsResponse,
)

logger = get_logger("services.srs")

# SM-2 constants
_MIN_EF: float = 1.30
_EASY_BONUS: float = 1.30
_HARD_INTERVAL_MULTIPLIER: float = 1.20
_GRADUATING_INTERVAL: int = 1
_EASY_GRADUATING_INTERVAL: int = 4
_MASTERY_INTERVAL_DAYS: int = 21


@dataclass(frozen=True)
class _CorpusContext:
    word_root: str | None = None
    word_pattern: str | None = None
    word_pos_tag: str | None = None
    transliteration: str | None = None
    example_surah_number: int | None = None
    example_ayah_number: int | None = None
    example_ayah_text: str | None = None
    example_ayah_translation: str | None = None


def _context_from_word(word: Word, verse: Verse, surah: Surah) -> _CorpusContext:
    return _CorpusContext(
        word_root=word.root,
        word_pattern=word.pattern,
        word_pos_tag=word.pos_tag,
        transliteration=word.transliteration,
        example_surah_number=surah.number,
        example_ayah_number=verse.ayah_number,
        example_ayah_text=verse.text_uthmani,
        example_ayah_translation=verse.translation_en,
    )


def _context_from_verse(verse: Verse, surah: Surah) -> _CorpusContext:
    return _CorpusContext(
        example_surah_number=surah.number,
        example_ayah_number=verse.ayah_number,
        example_ayah_text=verse.text_uthmani,
        example_ayah_translation=verse.translation_en,
    )


def _card_response(card: SRSCard, context: _CorpusContext | None = None) -> SRSCardResponse:
    context = context or _CorpusContext()
    return SRSCardResponse(
        id=card.id,
        item_type=card.item_type,
        front=card.front,
        back=card.back,
        hint=card.hint,
        word_id=card.word_id,
        deck_id=card.deck_id,
        surah_number=card.surah_number,
        ayah_number=card.ayah_number,
        state=card.state,
        ease_factor=card.ease_factor,
        interval_days=card.interval_days,
        repetitions=card.repetitions,
        lapses=card.lapses,
        due_date=card.due_date,
        last_reviewed_at=card.last_reviewed_at,
        word_root=context.word_root,
        word_pattern=context.word_pattern,
        word_pos_tag=context.word_pos_tag,
        transliteration=context.transliteration,
        example_surah_number=context.example_surah_number,
        example_ayah_number=context.example_ayah_number,
        example_ayah_text=context.example_ayah_text,
        example_ayah_translation=context.example_ayah_translation,
    )


def _sm2_schedule(
    card: SRSCard,
    rating: int,
    now: datetime,
) -> tuple[str, int, float, datetime]:
    """
    Apply SM-2 variant scheduling.  Returns (new_state, new_interval_days, new_ef, new_due_date).
    Rating: 1=Again, 2=Hard, 3=Good, 4=Easy
    """
    ef = card.ease_factor
    interval = card.interval_days
    reps = card.repetitions
    state = card.state

    if rating == 1:  # Again — lapse / reset
        new_state = "learning"
        new_interval = 1
        new_ef = max(_MIN_EF, ef - 0.20)
    elif state in ("new", "learning"):
        if rating == 4:  # Easy — graduate immediately with bonus
            new_interval = _EASY_GRADUATING_INTERVAL
            new_state = "review"
        elif reps == 0:
            new_interval = _GRADUATING_INTERVAL
            new_state = "learning"
        else:
            new_interval = _GRADUATING_INTERVAL + 1
            new_state = "review"
        new_ef = max(_MIN_EF, ef + (0.1 - (5 - rating) * (0.08 + (5 - rating) * 0.02)))
    else:  # review state
        if rating == 2:  # Hard
            new_interval = max(1, round(interval * _HARD_INTERVAL_MULTIPLIER))
            new_ef = max(_MIN_EF, ef - 0.15)
            new_state = "review"
        elif rating == 3:  # Good
            new_interval = max(1, round(interval * ef))
            new_ef = ef
            new_state = "review"
        else:  # Easy
            new_interval = max(1, round(interval * ef * _EASY_BONUS))
            new_ef = min(3.0, ef + 0.10)
            new_state = "review"

    if new_state == "review" and new_interval > _MASTERY_INTERVAL_DAYS:
        new_state = "graduated"

    new_due = now + timedelta(days=new_interval)
    return new_state, new_interval, round(new_ef, 4), new_due


class SRSService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _load_word_context(self, word_id: int) -> _CorpusContext | None:
        row = (
            await self.db.execute(
                select(Word, Verse, Surah)
                .join(Verse, Word.verse_id == Verse.id)
                .join(Surah, Verse.surah_id == Surah.id)
                .where(Word.id == word_id)
            )
        ).first()
        if row is None:
            return None
        word, verse, surah = row
        return _context_from_word(word, verse, surah)

    async def _load_contexts(self, cards: Sequence[SRSCard]) -> dict[int, _CorpusContext]:
        contexts: dict[int, _CorpusContext] = {}

        word_ids = {card.word_id for card in cards if card.word_id is not None}
        if word_ids:
            word_rows = (
                await self.db.execute(
                    select(Word, Verse, Surah)
                    .join(Verse, Word.verse_id == Verse.id)
                    .join(Surah, Verse.surah_id == Surah.id)
                    .where(Word.id.in_(word_ids))
                )
            ).all()
            contexts_by_word = {
                word.id: _context_from_word(word, verse, surah)
                for word, verse, surah in word_rows
            }
            for card in cards:
                if card.word_id is not None and card.word_id in contexts_by_word:
                    contexts[card.id] = contexts_by_word[card.word_id]

        refs = {
            (card.surah_number, card.ayah_number)
            for card in cards
            if card.word_id is None
            and card.surah_number is not None
            and card.ayah_number is not None
        }
        if refs:
            surah_numbers = {ref[0] for ref in refs}
            ayah_numbers = {ref[1] for ref in refs}
            verse_rows = (
                await self.db.execute(
                    select(Verse, Surah)
                    .join(Surah, Verse.surah_id == Surah.id)
                    .where(
                        Surah.number.in_(surah_numbers),
                        Verse.ayah_number.in_(ayah_numbers),
                    )
                )
            ).all()
            contexts_by_ref = {
                (surah.number, verse.ayah_number): _context_from_verse(verse, surah)
                for verse, surah in verse_rows
            }
            for card in cards:
                ref = (card.surah_number, card.ayah_number)
                if card.word_id is None and ref in contexts_by_ref:
                    contexts[card.id] = contexts_by_ref[ref]

        return contexts

    async def create_card(self, user_id: int, req: SRSCardCreate) -> SRSCardResponse:
        logger.info("Creating SRS card for user_id=%d type=%s", user_id, req.item_type)
        context: _CorpusContext | None = None
        if req.word_id is not None:
            context = await self._load_word_context(req.word_id)
            if context is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Word not found")

        surah_number = req.surah_number
        ayah_number = req.ayah_number
        if context is not None:
            if surah_number is None:
                surah_number = context.example_surah_number
            if ayah_number is None:
                ayah_number = context.example_ayah_number

        card = SRSCard(
            user_id=user_id,
            item_type=req.item_type,
            front=req.front,
            back=req.back,
            hint=req.hint,
            word_id=req.word_id,
            deck_id=req.deck_id,
            surah_number=surah_number,
            ayah_number=ayah_number,
        )
        self.db.add(card)
        await self.db.commit()
        await self.db.refresh(card)
        logger.info("Created card id=%d for user_id=%d", card.id, user_id)
        return _card_response(card, context)

    async def get_due_queue(
        self,
        user_id: int,
        limit: int = 20,
    ) -> SRSDueQueueResponse:
        now = datetime.now(UTC)
        logger.debug("Fetching due queue for user_id=%d limit=%d", user_id, limit)

        result = await self.db.execute(
            select(SRSCard)
            .where(
                SRSCard.user_id == user_id,
                SRSCard.state != "graduated",
                SRSCard.due_date <= now,
            )
            .order_by(SRSCard.due_date.asc())
            .limit(limit)
        )
        card_rows = list(result.scalars().all())
        contexts = await self._load_contexts(card_rows)

        new_count = sum(1 for c in card_rows if c.state == "new")
        learning_count = sum(1 for c in card_rows if c.state == "learning")
        review_count = sum(1 for c in card_rows if c.state == "review")

        logger.debug(
            "Due queue for user_id=%d: total=%d new=%d learning=%d review=%d",
            user_id,
            len(card_rows),
            new_count,
            learning_count,
            review_count,
        )
        return SRSDueQueueResponse(
            cards=[_card_response(c, contexts.get(c.id)) for c in card_rows],
            total=len(card_rows),
            new_count=new_count,
            learning_count=learning_count,
            review_count=review_count,
        )

    async def submit_review(
        self,
        user_id: int,
        card_id: int,
        rating: int,
        review_duration_ms: int | None,
    ) -> SRSReviewResponse:
        logger.info("Review submitted: user_id=%d card_id=%d rating=%d", user_id, card_id, rating)
        result = await self.db.execute(
            select(SRSCard).where(SRSCard.id == card_id, SRSCard.user_id == user_id)
        )
        card = result.scalar_one_or_none()
        if card is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")

        now = datetime.now(UTC)
        prev_interval = card.interval_days
        prev_ef = card.ease_factor

        new_state, new_interval, new_ef, new_due = _sm2_schedule(card, rating, now)

        if rating == 1:
            card.lapses += 1
        card.state = new_state
        card.interval_days = new_interval
        card.ease_factor = new_ef
        card.due_date = new_due
        card.repetitions += 1
        card.last_reviewed_at = now

        log = SRSReviewLog(
            card_id=card.id,
            user_id=user_id,
            rating=rating,
            review_duration_ms=review_duration_ms,
            previous_interval_days=prev_interval,
            new_interval_days=new_interval,
            previous_ease_factor=prev_ef,
            new_ease_factor=new_ef,
            reviewed_at=now,
        )
        self.db.add(log)

        from app.services.progress_service import ProgressService

        await ProgressService(self.db).apply_review_progress(user_id, rating, now.date())

        await self.db.commit()
        await self.db.refresh(card)

        logger.info(
            "Card id=%d advanced: state=%s interval=%d ef=%.2f due=%s",
            card.id,
            new_state,
            new_interval,
            new_ef,
            new_due.isoformat(),
        )
        return SRSReviewResponse(
            card_id=card.id,
            new_state=new_state,
            new_interval_days=new_interval,
            new_ease_factor=new_ef,
            next_due=new_due,
        )

    async def get_stats(self, user_id: int) -> SRSStatsResponse:
        logger.debug("Fetching SRS stats for user_id=%d", user_id)
        now = datetime.now(UTC)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        counts_result = await self.db.execute(
            select(SRSCard.state, func.count(SRSCard.id))
            .where(SRSCard.user_id == user_id)
            .group_by(SRSCard.state)
        )
        state_counts: dict[str, int] = {row[0]: row[1] for row in counts_result.all()}

        due_result = await self.db.execute(
            select(func.count(SRSCard.id)).where(
                SRSCard.user_id == user_id,
                SRSCard.state != "graduated",
                SRSCard.due_date <= now,
            )
        )
        due_now = due_result.scalar_one() or 0

        reviews_today_result = await self.db.execute(
            select(func.count(SRSReviewLog.id)).where(
                SRSReviewLog.user_id == user_id,
                SRSReviewLog.reviewed_at >= today_start,
            )
        )
        reviews_today = reviews_today_result.scalar_one() or 0

        user = (await self.db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
        streak = user.streak_days if user is not None else 0

        total = sum(state_counts.values())
        return SRSStatsResponse(
            total_cards=total,
            new_cards=state_counts.get("new", 0),
            learning_cards=state_counts.get("learning", 0),
            review_cards=state_counts.get("review", 0),
            graduated_cards=state_counts.get("graduated", 0),
            reviews_today=reviews_today,
            streak_days=streak,
            due_now=due_now,
        )

    async def delete_card(self, user_id: int, card_id: int) -> None:
        result = await self.db.execute(
            select(SRSCard).where(SRSCard.id == card_id, SRSCard.user_id == user_id)
        )
        card = result.scalar_one_or_none()
        if card is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")
        await self.db.delete(card)
        await self.db.commit()
        logger.info("Deleted SRS card id=%d for user_id=%d", card_id, user_id)
