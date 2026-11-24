from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.deck import Deck
from app.models.path import Lesson, QuizAttempt
from app.models.srs import SRSCard
from app.services.lesson_seed import seed_lessons

TINY_BANDS = {
    "beginner": (1, 2),
    "intermediate": (3, 3),
    "advanced": (4, 4),
}


async def _seed(db: AsyncSession) -> tuple[int, str]:
    await seed_lessons(db, bands=TINY_BANDS, min_occurrences=1)
    await db.commit()
    lesson = (
        await db.execute(
            select(Lesson)
            .where(Lesson.level == "beginner")
            .order_by(Lesson.sequence)
            .limit(1)
        )
    ).scalar_one()
    return lesson.id, lesson.title


async def _start(client, auth_headers, lesson_id: int) -> dict:
    response = await client.post(
        f"/api/v1/path/lessons/{lesson_id}/quiz", headers=auth_headers
    )
    assert response.status_code == 200
    return response.json()


async def _answers(
    db: AsyncSession, body: dict, correct_indexes: set[int] | None = None
) -> list[dict[str, object]]:
    correct_indexes = correct_indexes or set()
    attempt = (
        await db.execute(
            select(QuizAttempt).where(QuizAttempt.id == body["attempt_id"])
        )
    ).scalar_one()
    questions = {question["index"]: question for question in body["questions"]}
    answers: list[dict[str, object]] = []
    for item in attempt.answer_key_json:
        index = item["index"]
        correct = item["correct_option_id"]
        if index in correct_indexes:
            choice = correct
        else:
            choice = next(
                option["id"]
                for option in questions[index]["options"]
                if option["id"] != correct
            )
        answers.append({"index": index, "option_id": choice})
    return answers


async def _submit(client, auth_headers, body: dict, answers: list) -> dict:
    response = await client.post(
        f"/api/v1/path/quiz/{body['attempt_id']}/submit",
        json={"answers": answers},
        headers=auth_headers,
    )
    assert response.status_code == 200
    return response.json()


async def test_wrong_answers_create_cards_in_lesson_source_deck(
    client, auth_headers, db_session: AsyncSession, seed_quiz_data: None
) -> None:
    lesson_id, lesson_title = await _seed(db_session)
    body = await _start(client, auth_headers, lesson_id)
    result = await _submit(client, auth_headers, body, await _answers(db_session, body))

    assert result["score"] == 0
    assert len(result["srs_card_ids"]) == 5
    assert len(set(result["srs_card_ids"])) == 4

    db_session.expire_all()
    decks = (await db_session.execute(select(Deck))).scalars().all()
    assert len(decks) == 1
    assert decks[0].name == f"Lesson: {lesson_title}"
    assert decks[0].is_default is False
    cards = (
        await db_session.execute(
            select(SRSCard).order_by(SRSCard.id)
        )
    ).scalars().all()
    assert len(cards) == 4
    assert {card.id for card in cards} == set(result["srs_card_ids"])
    assert all(card.deck_id == decks[0].id for card in cards)
    assert {card.item_type for card in cards} == {
        "root",
        "vocabulary",
        "verse_fill_blank",
        "grammar_rule",
    }
    assert all(card.front and card.back for card in cards)
    assert all(card.surah_number == 1 for card in cards)
    assert {card.ayah_number for card in cards} == {1}


async def test_correct_answers_create_no_cards(
    client, auth_headers, db_session: AsyncSession, seed_quiz_data: None
) -> None:
    lesson_id, _ = await _seed(db_session)
    body = await _start(client, auth_headers, lesson_id)
    answers = await _answers(
        db_session, body, correct_indexes={1, 2, 3, 4, 5}
    )
    result = await _submit(client, auth_headers, body, answers)

    assert result["passed"] is True
    assert result["srs_card_ids"] == []
    db_session.expire_all()
    assert (
        await db_session.execute(select(func.count()).select_from(SRSCard))
    ).scalar_one() == 0
    assert (
        await db_session.execute(select(func.count()).select_from(Deck))
    ).scalar_one() == 0


async def test_only_wrong_answers_create_cards(
    client, auth_headers, db_session: AsyncSession, seed_quiz_data: None
) -> None:
    lesson_id, _ = await _seed(db_session)
    body = await _start(client, auth_headers, lesson_id)
    answers = await _answers(db_session, body, correct_indexes={1})
    result = await _submit(client, auth_headers, body, answers)

    assert len(result["srs_card_ids"]) == 4
    db_session.expire_all()
    cards = (await db_session.execute(select(SRSCard))).scalars().all()
    assert len(cards) == 4


async def test_repeating_the_same_mistakes_does_not_duplicate_cards(
    client, auth_headers, db_session: AsyncSession, seed_quiz_data: None
) -> None:
    lesson_id, _ = await _seed(db_session)
    first_body = await _start(client, auth_headers, lesson_id)
    first = await _submit(
        client, auth_headers, first_body, await _answers(db_session, first_body)
    )

    second_body = await _start(client, auth_headers, lesson_id)
    second = await _submit(
        client, auth_headers, second_body, await _answers(db_session, second_body)
    )

    assert set(second["srs_card_ids"]) == set(first["srs_card_ids"])
    db_session.expire_all()
    assert (
        await db_session.execute(select(func.count()).select_from(SRSCard))
    ).scalar_one() == 4


async def test_existing_source_deck_is_reused(
    client, auth_headers, db_session: AsyncSession, seed_quiz_data: None
) -> None:
    lesson_id, lesson_title = await _seed(db_session)
    db_session.add_all(
        [
            Deck(user_id=1, name="My Own Default", is_default=True),
            Deck(user_id=1, name=f"Lesson: {lesson_title}", is_default=False),
        ]
    )
    await db_session.commit()

    body = await _start(client, auth_headers, lesson_id)
    result = await _submit(client, auth_headers, body, await _answers(db_session, body))

    db_session.expire_all()
    decks = (await db_session.execute(select(Deck))).scalars().all()
    source_deck = next(
        deck for deck in decks if deck.name == f"Lesson: {lesson_title}"
    )
    cards = (await db_session.execute(select(SRSCard))).scalars().all()
    assert len(cards) == 4
    assert all(card.deck_id == source_deck.id for card in cards)
    assert len(set(result["srs_card_ids"])) == 4
