from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.srs import SRSCard, SRSReviewLog
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

    new_due = now + timedelta(days=new_interval)
    return new_state, new_interval, round(new_ef, 4), new_due


class SRSService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_card(self, user_id: int, req: SRSCardCreate) -> SRSCardResponse:
        logger.info("Creating SRS card for user_id=%d type=%s", user_id, req.item_type)
        card = SRSCard(
            user_id=user_id,
            item_type=req.item_type,
            front=req.front,
            back=req.back,
            hint=req.hint,
            word_id=req.word_id,
            surah_number=req.surah_number,
            ayah_number=req.ayah_number,
        )
        self.db.add(card)
        await self.db.commit()
        await self.db.refresh(card)
        logger.info("Created card id=%d for user_id=%d", card.id, user_id)
        return SRSCardResponse.model_validate(card)

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
                SRSCard.due_date <= now,
            )
            .order_by(SRSCard.due_date.asc())
            .limit(limit)
        )
        cards = list(result.scalars().all())

        new_count = sum(1 for c in cards if c.state == "new")
        learning_count = sum(1 for c in cards if c.state == "learning")
        review_count = sum(1 for c in cards if c.state == "review")

        logger.debug(
            "Due queue for user_id=%d: total=%d new=%d learning=%d review=%d",
            user_id, len(cards), new_count, learning_count, review_count,
        )
        return SRSDueQueueResponse(
            cards=[SRSCardResponse.model_validate(c) for c in cards],
            total=len(cards),
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
        logger.info(
            "Review submitted: user_id=%d card_id=%d rating=%d", user_id, card_id, rating
        )
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
        await self.db.commit()
        await self.db.refresh(card)

        logger.info(
            "Card id=%d advanced: state=%s interval=%d ef=%.2f due=%s",
            card.id, new_state, new_interval, new_ef, new_due.isoformat(),
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

        streak = await self._compute_streak(user_id, now)

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

    async def _compute_streak(self, user_id: int, now: datetime) -> int:
        result = await self.db.execute(
            select(func.date(SRSReviewLog.reviewed_at))
            .where(SRSReviewLog.user_id == user_id)
            .group_by(func.date(SRSReviewLog.reviewed_at))
            .order_by(func.date(SRSReviewLog.reviewed_at).desc())
        )
        review_dates = [row[0] for row in result.all()]

        if not review_dates:
            return 0

        streak = 0
        check_date = now.date()
        for d in review_dates:
            if isinstance(d, str):
                from datetime import date
                d = date.fromisoformat(d)
            if d == check_date:
                streak += 1
                check_date = check_date - timedelta(days=1)
            elif d < check_date:
                break
        return streak

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
