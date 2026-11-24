from __future__ import annotations

from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.path import Lesson, LessonWord, QuizAnswer, QuizAttempt
from app.models.quran import Word
from app.models.srs import SRSReviewLog
from app.models.user import User
from app.schemas.srs import SRSCardCreate
from app.services.progress_service import ProgressService
from app.services.srs_service import SRSService


async def _user(db: AsyncSession) -> User:
    return (
        await db.execute(select(User).where(User.email == "talib@example.com"))
    ).scalar_one()


async def _lesson(db: AsyncSession, *, sequence: int, root: str) -> Lesson:
    lesson = Lesson(
        title=f"Root {root}",
        module="vocabulary",
        level="beginner",
        sequence=sequence,
        root=root,
        content_json={"root": root, "forms": [], "example": None},
        est_minutes=10,
    )
    db.add(lesson)
    await db.flush()
    return lesson


async def test_new_user_path_and_progress_are_empty_but_valid(
    client, auth_headers
) -> None:
    plan = await client.get("/api/v1/path/plan", headers=auth_headers)
    assert plan.status_code == 200
    assert plan.json()["next_items"] == []

    response = await client.get("/api/v1/path/progress", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["words_learned"] == 0
    assert body["roots_learned"] == 0
    assert body["quiz_scores_over_time"] == []
    assert body["srs"]["total_cards"] == 0
    assert body["srs"]["streak_days"] == 0
    assert body["streak_days"] == 0


async def test_one_correct_quiz_updates_next_items_and_progress(
    client, auth_headers, db_session: AsyncSession, seed_quran_data: None
) -> None:
    user = await _user(db_session)
    words = (
        await db_session.execute(select(Word).order_by(Word.id))
    ).scalars().all()
    first = await _lesson(db_session, sequence=1, root=words[0].root or "رحم")
    second = await _lesson(db_session, sequence=2, root=words[2].root or "حمد")
    db_session.add_all(
        [
            LessonWord(lesson_id=first.id, word_id=words[0].id, sort_order=1),
            LessonWord(lesson_id=first.id, word_id=words[1].id, sort_order=2),
            LessonWord(lesson_id=second.id, word_id=words[2].id, sort_order=1),
            LessonWord(lesson_id=second.id, word_id=words[3].id, sort_order=2),
        ]
    )
    await db_session.flush()
    attempt = QuizAttempt(
        user_id=user.id,
        lesson_id=first.id,
        kind="lesson",
        seed=42,
        questions_json=[],
        answer_key_json=[
            {
                "index": 1,
                "item_type": "root",
                "correct_option_id": "a",
                "word_id": words[0].id,
                "verse_id": words[0].verse_id,
            },
            {
                "index": 2,
                "item_type": "meaning",
                "correct_option_id": "b",
                "word_id": words[2].id,
                "verse_id": words[2].verse_id,
            },
        ],
        status="submitted",
        score=1,
        total=2,
        completed_at=datetime(2026, 11, 24, 9, 0, tzinfo=UTC),
    )
    db_session.add(attempt)
    await db_session.flush()
    db_session.add_all(
        [
            QuizAnswer(
                attempt_id=attempt.id,
                question_index=1,
                option_id="a",
                is_correct=True,
            ),
            QuizAnswer(
                attempt_id=attempt.id,
                question_index=2,
                option_id="wrong",
                is_correct=False,
            ),
        ]
    )
    await db_session.commit()

    plan = await client.get("/api/v1/path/plan", headers=auth_headers)
    assert plan.status_code == 200
    items = plan.json()["next_items"]
    assert [item["word_id"] for item in items] == [
        words[1].id,
        words[2].id,
        words[3].id,
    ]
    assert [item["lesson_id"] for item in items] == [
        first.id,
        second.id,
        second.id,
    ]
    assert all(item["text_uthmani"] for item in items)

    response = await client.get("/api/v1/path/progress", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["words_learned"] == 1
    assert body["roots_learned"] == 1
    series = body["quiz_scores_over_time"]
    assert len(series) == 1
    assert series[0]["attempt_id"] == attempt.id
    assert (series[0]["score"], series[0]["total"], series[0]["passed"]) == (
        1,
        2,
        False,
    )
    assert series[0]["completed_at"] is not None


async def test_srs_reviews_feed_progress_and_are_reused_not_copied(
    client, auth_headers, db_session: AsyncSession, seed_quran_data: None
) -> None:
    words = (
        await db_session.execute(select(Word).order_by(Word.id).limit(3))
    ).scalars().all()
    lesson = await _lesson(db_session, sequence=1, root=words[0].root or "سمو")
    db_session.add_all(
        [
            LessonWord(lesson_id=lesson.id, word_id=word.id, sort_order=index)
            for index, word in enumerate(words, start=1)
        ]
    )
    await db_session.commit()

    for word in words:
        created = await client.post(
            "/api/v1/srs/cards",
            json={
                "item_type": "vocabulary",
                "front": word.text_uthmani,
                "back": word.translation_en or "gloss",
                "word_id": word.id,
            },
            headers=auth_headers,
        )
        assert created.status_code == 201
        reviewed = await client.post(
            "/api/v1/srs/review",
            json={"card_id": created.json()["id"], "rating": 3},
            headers=auth_headers,
        )
        assert reviewed.status_code == 200

    plan = await client.get("/api/v1/path/plan", headers=auth_headers)
    assert plan.json()["next_items"] == []

    srs = await client.get("/api/v1/srs/stats", headers=auth_headers)
    progress = await client.get("/api/v1/path/progress", headers=auth_headers)
    assert progress.status_code == 200
    body = progress.json()
    assert body["srs"] == srs.json()
    assert body["srs"]["total_cards"] == 3
    assert body["srs"]["reviews_today"] == 3
    assert body["streak_days"] == body["srs"]["streak_days"] == 1


async def test_progress_streak_matches_srs_across_two_explicit_days(
    client, auth_headers, db_session: AsyncSession, seed_quran_data: None
) -> None:
    user = await _user(db_session)
    word = (
        await db_session.execute(select(Word).order_by(Word.id).limit(1))
    ).scalar_one()
    card = await SRSService(db_session).create_card(
        user.id,
        SRSCardCreate(
            item_type="vocabulary",
            front=word.text_uthmani,
            back=word.translation_en or "gloss",
            word_id=word.id,
        ),
    )
    first_day = date(2026, 11, 23)
    second_day = date(2026, 11, 24)
    progress_service = ProgressService(db_session)
    await progress_service.apply_activity(user.id, first_day)
    await progress_service.apply_activity(user.id, second_day)
    db_session.add_all(
        [
            SRSReviewLog(
                card_id=card.id,
                user_id=user.id,
                rating=3,
                reviewed_at=datetime(2026, 11, 23, 23, 59, tzinfo=UTC),
            ),
            SRSReviewLog(
                card_id=card.id,
                user_id=user.id,
                rating=3,
                reviewed_at=datetime(2026, 11, 24, 0, 1, tzinfo=UTC),
            ),
        ]
    )
    await db_session.commit()

    srs = await client.get("/api/v1/srs/stats", headers=auth_headers)
    progress = await client.get("/api/v1/path/progress", headers=auth_headers)
    assert progress.status_code == 200
    body = progress.json()
    assert body["streak_days"] == 2
    assert body["streak_days"] == srs.json()["streak_days"]
    assert body["last_activity_date"] == second_day.isoformat()
