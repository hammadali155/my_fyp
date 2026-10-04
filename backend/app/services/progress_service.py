from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.badge import Badge, UserBadge
from app.models.deck import Deck
from app.models.srs import SRSCard, SRSReviewLog
from app.models.user import User

logger = get_logger("services.progress")

XP_BY_RATING = {1: 2, 2: 5, 3: 10, 4: 15}

BADGE_CATALOG: list[dict[str, object]] = [
    {"slug": "first_review", "label": "First Review", "icon": "star", "criteria": {"type": "reviews", "value": 1}},
    {"slug": "streak_7", "label": "7-Day Streak", "icon": "flame", "criteria": {"type": "streak", "value": 7}},
    {"slug": "reviews_100", "label": "100 Reviews", "icon": "hundred", "criteria": {"type": "reviews", "value": 100}},
    {"slug": "cards_mastered_50", "label": "50 Cards Mastered", "icon": "trophy", "criteria": {"type": "mastered", "value": 50}},
    {"slug": "first_custom_deck", "label": "First Custom Deck", "icon": "layers", "criteria": {"type": "custom_deck", "value": 1}},
]


def compute_streak_update(last_review_date: date | None, current_streak: int, today: date) -> int:
    """Single source of truth for streak transitions.

    - No prior review -> streak starts at 1.
    - Same day -> unchanged.
    - Yesterday -> +1.
    - Older (missed day) -> reset to 1.
    """
    if last_review_date is None:
        return 1
    if last_review_date == today:
        return current_streak
    if last_review_date == today - timedelta(days=1):
        return current_streak + 1
    return 1


def xp_for_rating(rating: int) -> int:
    return XP_BY_RATING.get(rating, 0)


class ProgressService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def apply_review_progress(self, user_id: int, rating: int, reviewed_on: date) -> None:
        user = (await self.db.execute(select(User).where(User.id == user_id))).scalar_one()
        user.xp += xp_for_rating(rating)
        user.streak_days = compute_streak_update(user.last_review_date, user.streak_days, reviewed_on)
        user.last_review_date = reviewed_on
        await self.check_and_award_badges(user_id)

    async def get_badges(self, user_id: int) -> list[dict[str, object]]:
        await self._ensure_catalog()
        rows = (
            await self.db.execute(
                select(Badge, UserBadge)
                .outerjoin(
                    UserBadge,
                    (UserBadge.badge_id == Badge.id) & (UserBadge.user_id == user_id),
                )
                .order_by(Badge.id.asc())
            )
        ).all()
        return [
            {
                "slug": badge.slug,
                "label": badge.label,
                "icon": badge.icon,
                "criteria": badge.criteria_json,
                "earned": ub is not None,
                "earned_at": ub.earned_at if ub else None,
            }
            for badge, ub in rows
        ]

    async def check_and_award_badges(self, user_id: int) -> list[str]:
        await self._ensure_catalog()
        user = (await self.db.execute(select(User).where(User.id == user_id))).scalar_one()

        review_count = (
            await self.db.execute(select(func.count()).select_from(SRSReviewLog).where(SRSReviewLog.user_id == user_id))
        ).scalar_one()
        mastered_count = (
            await self.db.execute(
                select(func.count()).select_from(SRSCard).where(SRSCard.user_id == user_id, SRSCard.state == "graduated")
            )
        ).scalar_one()
        custom_deck_count = (
            await self.db.execute(
                select(func.count()).select_from(Deck).where(Deck.user_id == user_id, Deck.is_default.is_(False))
            )
        ).scalar_one()

        conditions = {
            "first_review": review_count >= 1,
            "streak_7": user.streak_days >= 7,
            "reviews_100": review_count >= 100,
            "cards_mastered_50": mastered_count >= 50,
            "first_custom_deck": custom_deck_count >= 1,
        }
        awarded: list[str] = []
        for slug, met in conditions.items():
            if not met:
                continue
            badge = (await self.db.execute(select(Badge).where(Badge.slug == slug))).scalar_one()
            exists = (
                await self.db.execute(
                    select(UserBadge.id).where(UserBadge.user_id == user_id, UserBadge.badge_id == badge.id)
                )
            ).scalar_one_or_none()
            if exists is None:
                self.db.add(UserBadge(user_id=user_id, badge_id=badge.id))
                awarded.append(slug)
                logger.info("Awarded badge %s to user_id=%d", slug, user_id)
        return awarded

    async def _ensure_catalog(self) -> None:
        existing = {slug for (slug,) in (await self.db.execute(select(Badge.slug))).all()}
        for entry in BADGE_CATALOG:
            if entry["slug"] not in existing:
                self.db.add(Badge(slug=entry["slug"], label=entry["label"], icon=entry["icon"], criteria_json=entry["criteria"]))
        await self.db.flush()
