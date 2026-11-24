from __future__ import annotations

import importlib.util
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import ModuleType

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_password
from app.models.badge import UserBadge
from app.models.deck import Deck
from app.models.path import QuizAnswer, QuizAttempt, UserLesson
from app.models.quran import Surah, Verse, Word
from app.models.srs import SRSCard, SRSReviewLog
from app.models.user import User
from app.services.lesson_seed import seed_lessons

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "seed_demo.py"
NOW = datetime(2026, 11, 24, 12, 0, tzinfo=UTC)
TINY_BANDS = {
    "beginner": (1, 8),
    "intermediate": (9, 9),
    "advanced": (10, 10),
}


def _load_seed_demo() -> ModuleType:
    spec = importlib.util.spec_from_file_location("seed_demo", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["seed_demo"] = module
    spec.loader.exec_module(module)
    return module


seed_demo_module = _load_seed_demo()


ROOTS = (
    "علم",
    "كتب",
    "قلم",
    "نور",
    "باب",
    "حكم",
    "رحم",
    "حمد",
    "سمع",
    "بصر",
    "قول",
    "عمل",
    "جعل",
    "ذكر",
    "شكر",
    "صبر",
)
POS = ("N", "ADJ", "PN", "V")
FORMS_PER_ROOT = 3


@pytest.fixture
async def demo_corpus(db_session: AsyncSession) -> None:
    surah = Surah(
        id=2,
        number=2,
        name_arabic="سورة الاختبار",
        name_transliteration="Al-Ikhtibar",
        name_english="The Test",
        revelation_place="Makkah",
        verse_count=1,
    )
    db_session.add(surah)
    await db_session.flush()

    tokens: list[str] = []
    words: list[Word] = []
    for root_index, root in enumerate(ROOTS):
        for form_index in range(FORMS_PER_ROOT):
            token = f"{root}{form_index + 1}"
            tokens.append(token)
            words.append(
                Word(
                    verse_id=100,
                    position=len(tokens),
                    text_uthmani=token,
                    text_imlaei=token,
                    translation_en=f"{root} gloss {form_index + 1}",
                    root=root,
                    lemma=f"{root} lemma {form_index + 1}",
                    pos_tag=POS[(root_index + form_index) % len(POS)],
                )
            )
    verse = Verse(
        id=100,
        surah_id=2,
        ayah_number=1,
        text_uthmani=" ".join(tokens),
        text_imlaei=" ".join(tokens),
        translation_en="Synthetic test verse",
        juz_number=1,
        hizb_number=1,
        page_number=1,
    )
    db_session.add(verse)
    await db_session.flush()
    db_session.add_all(words)
    await db_session.commit()

    await seed_lessons(db_session, bands=TINY_BANDS, min_occurrences=1)
    await db_session.commit()


async def _demo_user(db: AsyncSession) -> User:
    return (
        await db.execute(
            select(User).where(User.email == seed_demo_module.DEMO_EMAIL)
        )
    ).scalar_one()


async def _counts(db: AsyncSession, user_id: int) -> dict[str, int]:
    async def count(model, *where) -> int:
        return (
            await db.execute(
                select(func.count()).select_from(model).where(*where)
            )
        ).scalar_one()

    return {
        "users": await count(User, User.email == seed_demo_module.DEMO_EMAIL),
        "decks": await count(Deck, Deck.user_id == user_id),
        "cards": await count(SRSCard, SRSCard.user_id == user_id),
        "attempts": await count(QuizAttempt, QuizAttempt.user_id == user_id),
        "answers": await count(
            QuizAnswer,
            QuizAnswer.attempt_id.in_(
                select(QuizAttempt.id).where(QuizAttempt.user_id == user_id)
            ),
        ),
        "lessons": await count(UserLesson, UserLesson.user_id == user_id),
        "reviews": await count(
            SRSReviewLog, SRSReviewLog.user_id == user_id
        ),
        "badges": await count(UserBadge, UserBadge.user_id == user_id),
    }


@pytest.mark.parametrize(
    "url",
    [
        "postgresql+asyncpg://jawhar:secret@db.example.com:5432/jawhar",
        "postgresql://jawhar:secret@localhost/jawhar_prod",
        "mysql://root@10.0.0.5/jawhar",
    ],
)
def test_production_like_urls_are_refused(url: str) -> None:
    with pytest.raises(seed_demo_module.UnsafeDatabaseError):
        seed_demo_module.assert_safe_database_url(url)


@pytest.mark.parametrize(
    "url",
    [
        "sqlite+aiosqlite:///./jawhar.db",
        "sqlite:///:memory:",
        "postgresql+asyncpg://jawhar:secret@localhost/jawhar_dev",
        "postgresql+asyncpg://jawhar:secret@127.0.0.1/jawhar",
    ],
)
def test_local_and_sqlite_urls_are_allowed(url: str) -> None:
    seed_demo_module.assert_safe_database_url(url)


async def test_seed_demo_requires_a_corpus(db_session: AsyncSession) -> None:
    with pytest.raises(RuntimeError, match="corpus"):
        await seed_demo_module.seed_demo(db_session, now=NOW)


async def test_seed_demo_builds_a_screen_ready_account(
    db_session: AsyncSession, demo_corpus: None
) -> None:
    result = await seed_demo_module.seed_demo(db_session, now=NOW)

    user = await _demo_user(db_session)
    assert result.user_id == user.id
    assert result.email == seed_demo_module.DEMO_EMAIL
    assert verify_password(seed_demo_module.DEMO_PASSWORD, user.password_hash)
    assert user.onb_complete is True
    assert user.level == "beginner"
    assert user.streak_days >= 7
    assert user.last_activity_date == NOW.date()
    assert user.xp > 0

    decks = (
        await db_session.execute(
            select(Deck)
            .where(Deck.user_id == user.id, Deck.name.like("Demo:%"))
            .order_by(Deck.id)
        )
    ).scalars().all()
    assert len(decks) == 2
    assert result.decks == 2

    cards = (
        await db_session.execute(
            select(SRSCard, Word)
            .join(Word, SRSCard.word_id == Word.id)
            .where(
                SRSCard.user_id == user.id,
                SRSCard.deck_id.in_([deck.id for deck in decks]),
            )
        )
    ).all()
    assert len(cards) >= 10
    for card, word in cards:
        assert card.front == word.text_uthmani
        assert card.back == (word.translation_en or "")

    completed = (
        await db_session.execute(
            select(func.count())
            .select_from(UserLesson)
            .where(
                UserLesson.user_id == user.id,
                UserLesson.status == "completed",
            )
        )
    ).scalar_one()
    assert completed >= 3
    assert result.lessons_completed == completed

    attempts = (
        await db_session.execute(
            select(QuizAttempt)
            .where(
                QuizAttempt.user_id == user.id,
                QuizAttempt.kind == "lesson",
                QuizAttempt.status == "submitted",
            )
            .order_by(QuizAttempt.id)
        )
    ).scalars().all()
    assert len(attempts) >= 3
    assert any(attempt.score == attempt.total for attempt in attempts)
    assert any((attempt.score or 0) < attempt.total for attempt in attempts)
    assert result.quizzes == len(attempts)

    answers = (
        await db_session.execute(
            select(QuizAnswer)
            .join(QuizAttempt, QuizAnswer.attempt_id == QuizAttempt.id)
            .where(QuizAttempt.user_id == user.id)
        )
    ).scalars().all()
    assert any(answer.is_correct for answer in answers)
    assert any(not answer.is_correct for answer in answers)

    logs = (
        await db_session.execute(
            select(SRSReviewLog).where(SRSReviewLog.user_id == user.id)
        )
    ).scalars().all()
    assert len(logs) == 100
    assert result.reviews == 100
    days = {log.reviewed_at.date() for log in logs}
    assert len(days) >= 13
    assert min(days) >= NOW.date() - timedelta(days=13)
    assert max(days) <= NOW.date()

    due_now = (
        await db_session.execute(
            select(func.count())
            .select_from(SRSCard)
            .where(
                SRSCard.user_id == user.id,
                SRSCard.state != "graduated",
                SRSCard.due_date <= NOW,
            )
        )
    ).scalar_one()
    assert due_now >= 1

    graduated = (
        await db_session.execute(
            select(func.count())
            .select_from(SRSCard)
            .where(
                SRSCard.user_id == user.id,
                SRSCard.state == "graduated",
            )
        )
    ).scalar_one()
    assert graduated >= 10

    badges = (
        await db_session.execute(
            select(func.count())
            .select_from(UserBadge)
            .where(UserBadge.user_id == user.id)
        )
    ).scalar_one()
    assert badges >= 4

    login = seed_demo_module.format_demo_login(result)
    assert result.email in login
    assert result.password in login


async def test_seed_demo_is_idempotent(
    db_session: AsyncSession, demo_corpus: None
) -> None:
    first = await seed_demo_module.seed_demo(db_session, now=NOW)
    first_counts = await _counts(db_session, first.user_id)

    second = await seed_demo_module.seed_demo(db_session, now=NOW)
    second_counts = await _counts(db_session, second.user_id)

    assert first.user_id == second.user_id
    assert first_counts == second_counts
    assert second_counts["users"] == 1
    assert second_counts["decks"] >= 2
    assert second_counts["reviews"] == 100
