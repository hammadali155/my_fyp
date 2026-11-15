from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.models.quran import NahwAnnotation


@pytest.mark.asyncio
async def test_get_verse_annotations_success(client: AsyncClient, seed_quran_data, db_session):
    db_session.add(NahwAnnotation(verse_id=1, word_id=1, token_index=1, role="فاعل", dep_type="Subj", head_index=-1, irab="مرفوع", sentence_index=1))
    await db_session.commit()
    resp = await client.get("/api/v1/nahw/verse/1/1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["surah_number"] == 1
    assert data["ayah_number"] == 1
    assert data["has_annotations"] is True
    assert len(data["tokens"]) == 1


@pytest.mark.asyncio
async def test_get_verse_annotations_cross_verse_head_carries_its_verse(
    client: AsyncClient, seed_quran_data, db_session
):
    db_session.add(
        NahwAnnotation(
            verse_id=2,
            word_id=5,
            token_index=1,
            role="مضاف إليه",
            dep_type="Poss",
            head_index=2,
            head_surah_number=1,
            head_ayah_number=1,
            irab="مجرور",
            sentence_index=1,
        )
    )
    await db_session.commit()

    resp = await client.get("/api/v1/nahw/verse/1/2")

    assert resp.status_code == 200
    token = resp.json()["tokens"][0]
    assert token["head_index"] == 2
    assert token["head_surah_number"] == 1
    assert token["head_ayah_number"] == 1


@pytest.mark.asyncio
async def test_get_verse_annotation_role_key_uses_the_legend(
    client: AsyncClient, seed_quran_data, db_session
):
    db_session.add(
        NahwAnnotation(
            verse_id=1,
            word_id=1,
            token_index=1,
            role="مضاف إليه",
            dep_type="Poss",
            head_index=-1,
            irab="مجرور",
            sentence_index=1,
        )
    )
    await db_session.commit()

    resp = await client.get("/api/v1/nahw/verse/1/1")

    assert resp.status_code == 200
    token = resp.json()["tokens"][0]
    assert token["role_ar"] == "مضاف إليه"
    assert token["role_key"] == "mudaf_ilayhi"
    assert token["role_en"] == "Mudaf ilayhi (possessor)"


@pytest.mark.asyncio
async def test_get_verse_annotations_404_unknown_verse(client: AsyncClient, seed_quran_data):
    resp = await client.get("/api/v1/nahw/verse/999/1")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_verse_annotations_empty_response_no_guess(client: AsyncClient, seed_quran_data):
    # verse exists but has no treebank data yet
    resp = await client.get("/api/v1/nahw/verse/1/2")
    assert resp.status_code == 200
    data = resp.json()
    assert data["tokens"] == []
    assert data["has_annotations"] is False
    assert "treebank" in data["message"].lower()


@pytest.mark.asyncio
async def test_get_verse_annotations_422_bad_input(client: AsyncClient, seed_quran_data):
    resp = await client.get("/api/v1/nahw/verse/abc/1")
    assert resp.status_code == 422
    resp = await client.get("/api/v1/nahw/verse/1/xyz")
    assert resp.status_code == 422
