#!/usr/bin/env python3
"""Create or refresh the demo learner account with data for every app screen.

All Arabic text and Quranic references are read from the corpus tables. The
script refuses to touch a database URL that looks like production and replaces
only the demo account's own data on reruns.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import urlsplit

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi import HTTPException, status  # noqa: E402
from sqlalchemy import delete, func, select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.core.logging import get_logger, setup_logging  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.db.session import async_session_factory, engine  # noqa: E402
from app.models.badge import UserBadge  # noqa: E402
from app.models.bookmark import Bookmark  # noqa: E402
from app.models.chat import ChatMessage, ChatSession  # noqa: E402
from app.models.deck import Deck  # noqa: E402
from app.models.path import (  # noqa: E402
    AssessmentAttempt,
    Lesson,
    QuizAnswer,
    QuizAttempt,
    UserLesson,
)
from app.models.quran import Word  # noqa: E402
from app.models.srs import SRSCard, SRSReviewLog  # noqa: E402
from app.models.user import RefreshToken, User  # noqa: E402
from app.schemas.deck import DeckCreate  # noqa: E402
from app.schemas.path import QuizAnswerRequest  # noqa: E402
from app.services.deck_service import DeckService  # noqa: E402
from app.services.frequency_service import PLACEHOLDER_ROOT  # noqa: E402
from app.services.lesson_seed import seed_lessons  # noqa: E402
from app.services.path_service import LESSON_COMPLETE_XP, PathService  # noqa: E402
from app.services.progress_service import XP_BY_RATING, ProgressService  # noqa: E402
from app.services.quiz_service import XP_PER_CORRECT, QuizService  # noqa: E402

logger = get_logger("scripts.seed_demo")

DEMO_EMAIL = "demo@jawhar.app"
DEMO_PASSWORD = "JawharDemo123!"
DEMO_NAME = "Demo Learner"
DECK_NAMES = ("Demo: Quranic Essentials", "Demo: Quranic Review")
DECK_SIZE = 30
QUIZ_SCORES = (5, 4, 3, 4, 2)
COMPLETED_LESSONS = 4
TOTAL_REVIEWS = 100
REVIEW_DAYS = 14
TARGET_STREAK = 14
MAX_GRADUATED = 50
MIN_ACTIVE_CARDS = 10


class UnsafeDatabaseError(RuntimeError):
    pass


@dataclass(frozen=True)
class DemoSeedResult:
    user_id: int
    email: str
    password: str
    decks: int
    cards: int
    lessons_completed: int
    quizzes: int
    reviews: int


def assert_safe_database_url(url: str) -> None:
    lowered = url.lower()
    if "prod" in lowered:
        raise UnsafeDatabaseError(
            f"Refusing to seed demo data into a production-looking database: {url}"
        )
    if lowered.startswith("sqlite"):
        return
    host = urlsplit(url).hostname
    if host in {None, "", "localhost", "127.0.0.1", "::1", "0.0.0.0"}:
        return
    raise UnsafeDatabaseError(
        f"Refusing to seed demo data into a remote database: {url}"
    )


def format_demo_login(result: DemoSeedResult) -> str:
    return (
        "Demo login\n"
        f"  Email:    {result.email}\n"
        f"  Password: {result.password}\n"
        f"  Data:     {result.decks} decks, {result.cards} cards, "
        f"{result.lessons_completed} lessons, {result.quizzes} quizzes, "
        f"{result.reviews} reviews"
    )


async def _prepare_user(
    db: AsyncSession, email: str, password: str
) -> User:
    user = (
        await db.execute(select(User).where(User.email == email))
    ).scalar_one_or_none()
    if user is None:
        user = User(
            email=email,
            name=DEMO_NAME,
            password_hash=hash_password(password),
        )
        db.add(user)
        await db.flush()
    else:
        user.name = DEMO_NAME
        user.password_hash = hash_password(password)
    user.role = "user"
    user.native_lang = "en"
    user.ui_lang = "en"
    user.level = "beginner"
    user.learning_goal = "quran"
    user.streak_days = 0
    user.last_review_date = None
    user.last_activity_date = None
    user.xp = 0
    user.is_active = True
    user.onb_complete = True
    await db.commit()
    return user


async def _clear_demo_data(db: AsyncSession, user_id: int) -> None:
    attempt_ids = select(QuizAttempt.id).where(QuizAttempt.user_id == user_id)
    session_ids = select(ChatSession.id).where(ChatSession.user_id == user_id)
    await db.execute(delete(SRSReviewLog).where(SRSReviewLog.user_id == user_id))
    await db.execute(delete(SRSCard).where(SRSCard.user_id == user_id))
    await db.execute(
        delete(QuizAnswer).where(QuizAnswer.attempt_id.in_(attempt_ids))
    )
    await db.execute(delete(QuizAttempt).where(QuizAttempt.user_id == user_id))
    await db.execute(
        delete(AssessmentAttempt).where(AssessmentAttempt.user_id == user_id)
    )
    await db.execute(delete(UserLesson).where(UserLesson.user_id == user_id))
    await db.execute(delete(UserBadge).where(UserBadge.user_id == user_id))
    await db.execute(delete(Bookmark).where(Bookmark.user_id == user_id))
    await db.execute(
        delete(ChatMessage).where(ChatMessage.session_id.in_(session_ids))
    )
    await db.execute(delete(ChatSession).where(ChatSession.user_id == user_id))
    await db.execute(
        delete(RefreshToken).where(RefreshToken.user_id == user_id)
    )
    await db.execute(delete(Deck).where(Deck.user_id == user_id))
    await db.commit()


async def _ensure_lessons(db: AsyncSession) -> None:
    count = (
        await db.execute(select(func.count()).select_from(Lesson))
    ).scalar_one()
    if count == 0:
        await seed_lessons(db)
        await db.commit()


async def _pick_word_ids(db: AsyncSession, target: int) -> list[int]:
    roots = (
        await db.execute(
            select(Word.root, func.count(Word.id).label("occurrences"))
            .where(Word.root.is_not(None), Word.root != PLACEHOLDER_ROOT)
            .group_by(Word.root)
            .order_by(func.count(Word.id).desc(), Word.root.asc())
            .limit(target * 2)
        )
    ).all()
    word_ids: list[int] = []
    for root, _ in roots:
        word_id = (
            await db.execute(
                select(Word.id)
                .where(
                    Word.root == root,
                    Word.translation_en.is_not(None),
                    Word.translation_en != "",
                )
                .order_by(Word.id.asc())
                .limit(1)
            )
        ).scalar_one_or_none()
        if word_id is not None:
            word_ids.append(word_id)
        if len(word_ids) >= target:
            break
    return word_ids


async def _seed_decks(db: AsyncSession, user: User) -> int:
    target = DECK_SIZE * len(DECK_NAMES)
    word_ids = await _pick_word_ids(db, target)
    if len(word_ids) < 2:
        raise RuntimeError(
            "The Quran corpus has too few usable words; run "
            "scripts/ingest_quran.py first."
        )
    service = DeckService(db)
    for index, name in enumerate(DECK_NAMES):
        response = await service.create_deck(user.id, DeckCreate(name=name))
        chunk = word_ids[index::len(DECK_NAMES)]
        if chunk:
            await service.add_words(user.id, response.id, chunk)
    return len(word_ids)


async def _band_lessons(
    db: AsyncSession, user: User, limit: int
) -> list[Lesson]:
    return list(
        (
            await db.execute(
                select(Lesson)
                .where(Lesson.level == user.level)
                .order_by(Lesson.sequence.asc(), Lesson.id.asc())
                .limit(limit)
            )
        )
        .scalars()
        .all()
    )


async def _complete_lessons(
    db: AsyncSession, user: User, lessons: list[Lesson], now: datetime
) -> int:
    path = PathService(db)
    completed: list[Lesson] = []
    for lesson in lessons:
        await path.complete_lesson(user, lesson.id)
        completed.append(lesson)
    rows = (
        await db.execute(
            select(UserLesson)
            .where(
                UserLesson.user_id == user.id,
                UserLesson.lesson_id.in_([lesson.id for lesson in completed]),
            )
            .order_by(UserLesson.lesson_id.asc())
        )
    ).scalars().all()
    for index, row in enumerate(rows):
        row.completed_at = now - timedelta(days=len(rows) - 1 - index)
    await db.commit()
    return len(completed)


async def _run_quizzes(
    db: AsyncSession,
    user: User,
    lessons: list[Lesson],
    now: datetime,
) -> list[int]:
    quiz = QuizService(db)
    scores: list[int] = []
    for lesson in lessons:
        if len(scores) >= len(QUIZ_SCORES):
            break
        target = QUIZ_SCORES[len(scores)]
        try:
            started = await quiz.start_lesson_quiz(user, lesson.id)
        except HTTPException as exc:
            if exc.status_code == status.HTTP_409_CONFLICT:
                logger.warning(
                    "Skipping quiz for lesson_id=%d: %s", lesson.id, exc.detail
                )
                continue
            raise
        attempt = (
            await db.execute(
                select(QuizAttempt).where(QuizAttempt.id == started.attempt_id)
            )
        ).scalar_one()
        key = {
            int(item["index"]): item for item in attempt.answer_key_json
        }
        options = {
            int(question["index"]): {
                str(option["id"]) for option in question["options"]
            }
            for question in attempt.questions_json
        }
        answers: list[QuizAnswerRequest] = []
        for position, index in enumerate(sorted(key)):
            correct = str(key[index]["correct_option_id"])
            chosen = correct
            if position >= target:
                chosen = next(
                    option for option in options[index] if option != correct
                )
            answers.append(QuizAnswerRequest(index=index, option_id=chosen))
        result = await quiz.submit_quiz(user, started.attempt_id, answers)
        attempt.completed_at = now - timedelta(
            days=len(QUIZ_SCORES) - 1 - len(scores)
        )
        row = (
            await db.execute(
                select(UserLesson).where(
                    UserLesson.user_id == user.id,
                    UserLesson.lesson_id == lesson.id,
                )
            )
        ).scalar_one_or_none()
        if row is not None:
            row.score = float(result.score)
        await db.commit()
        scores.append(result.score)
    return scores


async def _seed_review_history(
    db: AsyncSession, user: User, now: datetime
) -> tuple[int, int, list[SRSReviewLog]]:
    cards = list(
        (
            await db.execute(
                select(SRSCard)
                .where(SRSCard.user_id == user.id)
                .order_by(SRSCard.id.asc())
            )
        )
        .scalars()
        .all()
    )
    if not cards:
        raise RuntimeError("No SRS cards were created for the demo account.")
    total = len(cards)
    graduated = min(MAX_GRADUATED, max(0, total - MIN_ACTIVE_CARDS))
    reviewing = min(10, total - graduated)
    learning = min(5, total - graduated - reviewing)

    for index, card in enumerate(cards):
        if index < graduated:
            interval = 30 + (index % 60)
            card.state = "graduated"
            card.interval_days = interval
            card.ease_factor = round(2.5 + (index % 5) * 0.1, 2)
            card.repetitions = 4 + (index % 3)
            card.lapses = index % 2
            card.due_date = now + timedelta(days=interval)
            card.last_reviewed_at = now - timedelta(days=1 + (index % 13))
        elif index < graduated + reviewing:
            interval = 3 + (index % 8)
            card.state = "review"
            card.interval_days = interval
            card.ease_factor = round(2.3 + (index % 4) * 0.1, 2)
            card.repetitions = 2 + (index % 3)
            card.lapses = index % 3
            card.due_date = (
                now - timedelta(hours=1)
                if index % 2 == 0
                else now + timedelta(days=(index % 6) + 1)
            )
            card.last_reviewed_at = now - timedelta(days=1 + (index % 10))
        elif index < graduated + reviewing + learning:
            card.state = "learning"
            card.interval_days = 1
            card.ease_factor = 2.5
            card.repetitions = 1
            card.lapses = 0
            card.due_date = now - timedelta(hours=2)
            card.last_reviewed_at = now - timedelta(days=1)
        else:
            card.state = "new"
            card.interval_days = 0
            card.ease_factor = 2.5
            card.repetitions = 0
            card.lapses = 0
            card.due_date = now - timedelta(minutes=5)
            card.last_reviewed_at = None

    reviewed_cards = cards[: graduated + reviewing + learning]
    ratings = (4, 3, 3, 2, 4, 3, 1, 4, 3, 2)
    logs: list[SRSReviewLog] = []
    for index in range(TOTAL_REVIEWS):
        card = reviewed_cards[index % len(reviewed_cards)]
        day_offset = (REVIEW_DAYS - 1) - (index % REVIEW_DAYS)
        reviewed_at = (now - timedelta(days=day_offset)).replace(
            minute=(index % 6) * 10, second=0, microsecond=0
        )
        if reviewed_at > now:
            reviewed_at = now
        rating = ratings[index % len(ratings)]
        logs.append(
            SRSReviewLog(
                card_id=card.id,
                user_id=user.id,
                rating=rating,
                review_duration_ms=2500 + (index * 137) % 9000,
                previous_interval_days=max(0, card.interval_days - 1),
                new_interval_days=card.interval_days,
                previous_ease_factor=max(1.3, card.ease_factor - 0.1),
                new_ease_factor=card.ease_factor,
                reviewed_at=reviewed_at,
            )
        )
    db.add_all(logs)
    await db.commit()
    return total, graduated, logs


async def _finalize_user(
    db: AsyncSession,
    user: User,
    lessons_completed: int,
    scores: list[int],
    logs: list[SRSReviewLog],
    now: datetime,
) -> None:
    review_xp = sum(XP_BY_RATING[log.rating] for log in logs)
    quiz_xp = sum(scores) * XP_PER_CORRECT
    lesson_xp = lessons_completed * LESSON_COMPLETE_XP
    user.xp = lesson_xp + quiz_xp + review_xp
    user.streak_days = TARGET_STREAK
    user.last_review_date = now.date()
    user.last_activity_date = now.date()
    await db.flush()
    await ProgressService(db).check_and_award_badges(user.id)
    await db.commit()


async def seed_demo(
    db: AsyncSession,
    *,
    now: datetime | None = None,
    email: str = DEMO_EMAIL,
    password: str = DEMO_PASSWORD,
) -> DemoSeedResult:
    moment = now or datetime.now(UTC)
    word_count = (
        await db.execute(select(func.count()).select_from(Word))
    ).scalar_one()
    if word_count == 0:
        raise RuntimeError(
            "The Quran corpus is empty; run scripts/ingest_quran.py first."
        )

    await _ensure_lessons(db)
    user = await _prepare_user(db, email, password)
    await _clear_demo_data(db, user.id)

    await _seed_decks(db, user)

    lessons = await _band_lessons(
        db, user, max(COMPLETED_LESSONS + 1, len(QUIZ_SCORES))
    )
    if not lessons:
        raise RuntimeError(
            f"No {user.level} lessons are available in the learning path."
        )
    complete_count = min(COMPLETED_LESSONS, len(lessons) - 1)
    completed = await _complete_lessons(
        db, user, lessons[:complete_count], moment
    )
    scores = await _run_quizzes(db, user, lessons, moment)
    total_cards, _graduated, logs = await _seed_review_history(
        db, user, moment
    )
    await _finalize_user(db, user, completed, scores, logs, moment)

    result = DemoSeedResult(
        user_id=user.id,
        email=user.email,
        password=password,
        decks=len(DECK_NAMES),
        cards=total_cards,
        lessons_completed=completed,
        quizzes=len(scores),
        reviews=len(logs),
    )
    logger.info(
        "Demo account ready: user_id=%d decks=%d cards=%d lessons=%d "
        "quizzes=%d reviews=%d",
        result.user_id,
        result.decks,
        result.cards,
        result.lessons_completed,
        result.quizzes,
        result.reviews,
    )
    return result


async def _run(args: argparse.Namespace) -> None:
    try:
        async with async_session_factory() as session:
            result = await seed_demo(
                session, email=args.email, password=args.password
            )
        print(format_demo_login(result))
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create or refresh the demo learner account"
    )
    parser.add_argument("--email", default=DEMO_EMAIL)
    parser.add_argument("--password", default=DEMO_PASSWORD)
    args = parser.parse_args()
    setup_logging(level="INFO")
    try:
        assert_safe_database_url(get_settings().database_url)
    except UnsafeDatabaseError as exc:
        raise SystemExit(str(exc)) from exc
    asyncio.run(_run(args))


if __name__ == "__main__":
    main()
