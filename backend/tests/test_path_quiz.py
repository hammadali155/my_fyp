from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.path import Lesson, QuizAnswer, QuizAttempt
from app.models.user import User
from app.services.lesson_seed import seed_lessons

TINY_BANDS = {
    "beginner": (1, 2),
    "intermediate": (3, 3),
    "advanced": (4, 4),
}


async def _seed(db: AsyncSession) -> dict[str, int]:
    await seed_lessons(db, bands=TINY_BANDS, min_occurrences=1)
    await db.commit()
    lessons = (
        await db.execute(
            select(Lesson)
            .where(Lesson.level == "beginner")
            .order_by(Lesson.sequence)
        )
    ).scalars().all()
    return {
        "first": lessons[0].id,
        "second": lessons[1].id,
    }


async def _start(client, auth_headers, lesson_id: int):
    return await client.post(
        f"/api/v1/path/lessons/{lesson_id}/quiz", headers=auth_headers
    )


async def test_start_quiz_returns_questions_without_answers(
    client, auth_headers, db_session: AsyncSession, seed_quiz_data: None
) -> None:
    ids = await _seed(db_session)

    response = await _start(client, auth_headers, ids["first"])
    assert response.status_code == 200
    body = response.json()
    assert body["attempt_id"] > 0
    assert body["lesson_id"] == ids["first"]
    assert body["total"] == 5
    assert len(body["questions"]) == 5
    assert "correct_option_id" not in response.text
    assert "correct_index" not in response.text
    assert "explanation" not in response.text
    assert "answer_key" not in response.text


async def test_locked_lesson_quiz_returns_409(
    client, auth_headers, db_session: AsyncSession, seed_quiz_data: None
) -> None:
    ids = await _seed(db_session)
    response = await _start(client, auth_headers, ids["second"])
    assert response.status_code == 409


async def test_quiz_start_requires_authentication(
    client, db_session: AsyncSession, seed_quiz_data: None
) -> None:
    ids = await _seed(db_session)
    response = await client.post(f"/api/v1/path/lessons/{ids['first']}/quiz")
    assert response.status_code == 401


async def test_submit_all_correct_awards_xp_and_passes(
    client, auth_headers, db_session: AsyncSession, seed_quiz_data: None
) -> None:
    ids = await _seed(db_session)
    attempt_id = (await _start(client, auth_headers, ids["first"])).json()[
        "attempt_id"
    ]
    attempt = (
        await db_session.execute(
            select(QuizAttempt).where(QuizAttempt.id == attempt_id)
        )
    ).scalar_one()
    answers = [
        {"index": item["index"], "option_id": item["correct_option_id"]}
        for item in attempt.answer_key_json
    ]

    response = await client.post(
        f"/api/v1/path/quiz/{attempt_id}/submit",
        json={"answers": answers},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["score"] == 5
    assert body["correct"] == 5
    assert body["passed"] is True
    assert body["xp_awarded"] == 10
    assert body["srs_card_ids"] == []
    assert all(result["correct"] for result in body["results"])

    db_session.expire_all()
    user = (await db_session.execute(select(User))).scalars().one()
    assert user.xp == 10
    assert user.streak_days == 1


async def test_submit_wrong_answers_fails_without_xp(
    client, auth_headers, db_session: AsyncSession, seed_quiz_data: None
) -> None:
    ids = await _seed(db_session)
    body = (await _start(client, auth_headers, ids["first"])).json()
    attempt = (
        await db_session.execute(
            select(QuizAttempt).where(QuizAttempt.id == body["attempt_id"])
        )
    ).scalar_one()
    key = {item["index"]: item["correct_option_id"] for item in attempt.answer_key_json}
    questions = {item["index"]: item for item in body["questions"]}
    answers = []
    for index, correct in key.items():
        wrong = next(
            option["id"]
            for option in questions[index]["options"]
            if option["id"] != correct
        )
        answers.append({"index": index, "option_id": wrong})

    response = await client.post(
        f"/api/v1/path/quiz/{body['attempt_id']}/submit",
        json={"answers": answers},
        headers=auth_headers,
    )
    assert response.status_code == 200
    result = response.json()
    assert result["score"] == 0
    assert result["passed"] is False
    assert result["xp_awarded"] == 0

    db_session.expire_all()
    user = (await db_session.execute(select(User))).scalars().one()
    assert user.xp == 0


async def test_second_submit_returns_409(
    client, auth_headers, db_session: AsyncSession, seed_quiz_data: None
) -> None:
    ids = await _seed(db_session)
    attempt_id = (await _start(client, auth_headers, ids["first"])).json()[
        "attempt_id"
    ]
    first = await client.post(
        f"/api/v1/path/quiz/{attempt_id}/submit",
        json={"answers": []},
        headers=auth_headers,
    )
    assert first.status_code == 200

    second = await client.post(
        f"/api/v1/path/quiz/{attempt_id}/submit",
        json={"answers": []},
        headers=auth_headers,
    )
    assert second.status_code == 409


async def test_submit_unknown_index_returns_422(
    client, auth_headers, db_session: AsyncSession, seed_quiz_data: None
) -> None:
    ids = await _seed(db_session)
    attempt_id = (await _start(client, auth_headers, ids["first"])).json()[
        "attempt_id"
    ]

    response = await client.post(
        f"/api/v1/path/quiz/{attempt_id}/submit",
        json={"answers": [{"index": 99, "option_id": "x"}]},
        headers=auth_headers,
    )
    assert response.status_code == 422


async def test_another_users_attempt_returns_404(
    client, auth_headers, db_session: AsyncSession, seed_quiz_data: None
) -> None:
    ids = await _seed(db_session)
    other = User(email="other@example.com", name="Other Learner", password_hash="x")
    db_session.add(other)
    await db_session.flush()
    attempt = QuizAttempt(
        user_id=other.id,
        lesson_id=ids["first"],
        kind="lesson",
        seed=1,
        questions_json=[],
        answer_key_json=[],
        total=0,
    )
    db_session.add(attempt)
    await db_session.commit()

    response = await client.post(
        f"/api/v1/path/quiz/{attempt.id}/submit",
        json={"answers": []},
        headers=auth_headers,
    )
    assert response.status_code == 404


async def test_submit_results_include_stored_explanations(
    client, auth_headers, db_session: AsyncSession, seed_quiz_data: None
) -> None:
    ids = await _seed(db_session)
    attempt_id = (await _start(client, auth_headers, ids["first"])).json()[
        "attempt_id"
    ]
    attempt = (
        await db_session.execute(
            select(QuizAttempt).where(QuizAttempt.id == attempt_id)
        )
    ).scalar_one()
    answers = [
        {"index": item["index"], "option_id": item["correct_option_id"]}
        for item in attempt.answer_key_json
    ]

    response = await client.post(
        f"/api/v1/path/quiz/{attempt_id}/submit",
        json={"answers": answers},
        headers=auth_headers,
    )
    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) == 5
    for result in results:
        explanation = result["explanation"]
        assert isinstance(explanation, str) and explanation
        assert result["correct_option_id"] in explanation

    db_session.expire_all()
    stored = (
        await db_session.execute(
            select(QuizAnswer)
            .where(QuizAnswer.attempt_id == attempt_id)
            .order_by(QuizAnswer.question_index)
        )
    ).scalars().all()
    assert [answer.explanation for answer in stored] == [
        result["explanation"] for result in results
    ]


async def test_submit_requires_authentication(
    client, db_session: AsyncSession, seed_quiz_data: None
) -> None:
    response = await client.post(
        "/api/v1/path/quiz/999/submit", json={"answers": []}
    )
    assert response.status_code == 401
