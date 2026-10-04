from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _make_deck(client: AsyncClient, headers: dict, name: str = "My Deck") -> int:
    r = await client.post("/api/v1/decks", json={"name": name}, headers=headers)
    assert r.status_code == 201
    return r.json()["id"]


@pytest.mark.asyncio
async def test_deck_lifecycle(client: AsyncClient, auth_headers, seed_quran_data, db_session):
    deck_id = await _make_deck(client, auth_headers)

    r = await client.get("/api/v1/decks", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["total"] == 1
    assert r.json()["items"][0]["counts"] == {"new": 0, "learning": 0, "review": 0, "graduated": 0}

    from sqlalchemy import select

    from app.models.quran import Word

    word_id = (await db_session.execute(select(Word.id).limit(1))).scalar_one()
    r = await client.post(f"/api/v1/decks/{deck_id}/words", json={"word_id": word_id}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["added"] == 1

    r = await client.get("/api/v1/decks", headers=auth_headers)
    counts = r.json()["items"][0]["counts"]
    assert counts["new"] == 1
    assert r.json()["items"][0]["total_cards"] == 1

    r = await client.post(f"/api/v1/decks/{deck_id}/words", json={"word_id": word_id}, headers=auth_headers)
    assert r.status_code == 409

    all_ids = [w for (w,) in (await db_session.execute(select(Word.id))).all()]
    other_ids = [w for w in all_ids if w != word_id][:2]
    r = await client.post(f"/api/v1/decks/{deck_id}/words/bulk", json={"word_ids": other_ids + [word_id]}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["added"] == 2
    assert r.json()["skipped_duplicates"] == 1

    r = await client.delete(f"/api/v1/decks/{deck_id}", headers=auth_headers)
    assert r.status_code == 204
    r = await client.get("/api/v1/decks", headers=auth_headers)
    assert r.json()["total"] == 0


@pytest.mark.asyncio
async def test_deck_ownership(client: AsyncClient, auth_headers, seed_quran_data, db_session):
    deck_id = await _make_deck(client, auth_headers)
    other = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "deck-other@example.com",
            "name": "Other",
            "password": "SecurePassword123!",
            "native_lang": "en",
            "ui_lang": "en",
            "level": "beginner",
        },
    )
    other_headers = {"Authorization": f"Bearer {other.json()['tokens']['access_token']}"}

    r = await client.get("/api/v1/decks", headers=other_headers)
    assert r.json()["total"] == 0

    from sqlalchemy import select

    from app.models.quran import Word

    word_id = (await db_session.execute(select(Word.id).limit(1))).scalar_one()
    r = await client.post(f"/api/v1/decks/{deck_id}/words", json={"word_id": word_id}, headers=other_headers)
    assert r.status_code == 404
    r = await client.delete(f"/api/v1/decks/{deck_id}", headers=other_headers)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_deck_requires_auth(client: AsyncClient):
    r = await client.get("/api/v1/decks")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_seed_default_deck(client: AsyncClient, auth_headers, seed_quran_data, db_session):
    import sys
    from pathlib import Path

    scripts = Path(__file__).resolve().parent.parent.parent / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    import seed_default_deck
    from sqlalchemy import func, select

    from app.models.deck import Deck
    from app.models.srs import SRSCard

    added, skipped = await seed_default_deck.seed_for_user(db_session, 1, limit=2)
    assert added == 2
    assert skipped == 0

    deck = (await db_session.execute(select(Deck).where(Deck.user_id == 1))).scalar_one()
    assert deck.name == seed_default_deck.DEFAULT_NAME
    assert deck.is_default is True

    cards = (await db_session.execute(select(SRSCard).where(SRSCard.deck_id == deck.id))).scalars().all()
    assert len(cards) == 2
    from app.models.quran import Word

    for card in cards:
        word = (await db_session.execute(select(Word).where(Word.id == card.word_id))).scalar_one()
        assert card.front == word.text_uthmani
        assert card.back == (word.translation_en or "")
        assert card.hint == word.root

    added2, skipped2 = await seed_default_deck.seed_for_user(db_session, 1, limit=2)
    assert added2 == 0
    assert skipped2 == 2
    total = (await db_session.execute(select(func.count()).select_from(SRSCard))).scalar_one()
    assert total == 2
