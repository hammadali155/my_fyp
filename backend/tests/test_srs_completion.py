from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quran import Verse, Word
from app.models.srs import SRSCard, SRSReviewLog
from app.models.user import User
from app.services.srs_service import _sm2_schedule


def _card(
    *,
    state: str = "new",
    ef: float = 2.50,
    interval: int = 0,
    reps: int = 0,
    due: datetime | None = None,
) -> SRSCard:
    return SRSCard(
        user_id=1,
        item_type="root",
        front="كتب",
        back="to write",
        state=state,
        ease_factor=ef,
        interval_days=interval,
        repetitions=reps,
        lapses=0,
        due_date=due or datetime.now(UTC),
    )


def test_review_interval_above_21_days_marks_card_graduated() -> None:
    card = _card(state="review", interval=20, reps=5)
    state, interval, _, _ = _sm2_schedule(card, 3, datetime.now(UTC))
    assert state == "graduated"
    assert interval == 50


async def test_due_queue_excludes_graduated_cards(
    client, auth_headers, db_session: AsyncSession
) -> None:
    user = (await db_session.execute(select(User).where(User.email == "talib@example.com"))).scalar_one()
    card = _card(state="graduated", due=datetime.now(UTC) - timedelta(days=1))
    card.user_id = user.id
    db_session.add(card)
    await db_session.commit()

    response = await client.get("/api/v1/srs/due", headers=auth_headers)
    assert response.status_code == 200
    assert card.id not in [item["id"] for item in response.json()["cards"]]


async def test_stats_count_graduated_without_treating_it_as_due(
    client, auth_headers, db_session: AsyncSession
) -> None:
    user = (await db_session.execute(select(User).where(User.email == "talib@example.com"))).scalar_one()
    card = _card(state="graduated", due=datetime.now(UTC) - timedelta(days=1))
    card.user_id = user.id
    db_session.add(card)
    await db_session.commit()

    response = await client.get("/api/v1/srs/stats", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["graduated_cards"] == 1
    assert body["due_now"] == 0


async def test_state_check_rejects_unknown_state(
    db_session: AsyncSession, registered_user: dict
) -> None:
    card = _card(state="mastered")
    card.user_id = int(registered_user["user"]["id"])
    db_session.add(card)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


async def test_rating_check_rejects_out_of_range(
    db_session: AsyncSession, registered_user: dict
) -> None:
    user_id = int(registered_user["user"]["id"])
    card = _card()
    card.user_id = user_id
    db_session.add(card)
    await db_session.flush()
    db_session.add(
        SRSReviewLog(
            card_id=card.id,
            user_id=user_id,
            rating=5,
            reviewed_at=datetime.now(UTC),
        )
    )
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


async def test_create_card_with_word_id_enriches_response_from_corpus(
    client,
    auth_headers,
    db_session: AsyncSession,
    seed_quran_data: None,
) -> None:
    word = (await db_session.execute(select(Word).where(Word.position == 3))).scalar_one()
    word.pattern = "فَعْلَان"
    verse = (await db_session.execute(select(Verse).where(Verse.id == word.verse_id))).scalar_one()
    await db_session.commit()

    response = await client.post(
        "/api/v1/srs/cards",
        headers=auth_headers,
        json={
            "item_type": "vocabulary",
            "front": word.text_uthmani,
            "back": word.translation_en,
            "word_id": word.id,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["word_root"] == "رحم"
    assert body["word_pattern"] == "فَعْلَان"
    assert body["word_pos_tag"] == "ADJ"
    assert body["transliteration"] == "l-rahmani"
    assert body["surah_number"] == 1
    assert body["ayah_number"] == 1
    assert body["example_surah_number"] == 1
    assert body["example_ayah_number"] == 1
    assert body["example_ayah_text"] == verse.text_uthmani
    assert body["example_ayah_translation"] == verse.translation_en


async def test_create_card_rejects_unknown_word_id(
    client, auth_headers, seed_quran_data: None
) -> None:
    response = await client.post(
        "/api/v1/srs/cards",
        headers=auth_headers,
        json={"front": "كلمة", "back": "word", "word_id": 999999},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Word not found"


async def test_create_custom_card_without_word_id_has_no_corpus_fields(
    client, auth_headers
) -> None:
    response = await client.post(
        "/api/v1/srs/cards",
        headers=auth_headers,
        json={"front": "Custom front", "back": "Custom back"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["word_root"] is None
    assert body["word_pattern"] is None
    assert body["word_pos_tag"] is None
    assert body["transliteration"] is None
    assert body["example_surah_number"] is None
    assert body["example_ayah_number"] is None
    assert body["example_ayah_text"] is None
    assert body["example_ayah_translation"] is None


async def test_due_queue_enriches_cards_from_corpus(
    client, auth_headers, db_session: AsyncSession, seed_quran_data: None
) -> None:
    user = (await db_session.execute(select(User).where(User.email == "talib@example.com"))).scalar_one()
    word = (
        await db_session.execute(select(Word).where(Word.text_uthmani == "ٱلْحَمْدُ"))
    ).scalar_one()
    verse = (await db_session.execute(select(Verse).where(Verse.id == word.verse_id))).scalar_one()
    card = _card(due=datetime.now(UTC) - timedelta(days=1))
    card.user_id = user.id
    card.word_id = word.id
    db_session.add(card)
    await db_session.commit()

    response = await client.get("/api/v1/srs/due", headers=auth_headers)

    assert response.status_code == 200
    item = next(c for c in response.json()["cards"] if c["id"] == card.id)
    assert item["word_root"] == "حمد"
    assert item["word_pos_tag"] == "N"
    assert item["transliteration"] == "al-hamdu"
    assert item["example_surah_number"] == 1
    assert item["example_ayah_number"] == 2
    assert item["example_ayah_text"] == verse.text_uthmani
    assert item["example_ayah_translation"] == verse.translation_en
