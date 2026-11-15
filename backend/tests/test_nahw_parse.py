from __future__ import annotations

import httpx
import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.quran import NahwAnnotation, Verse, Word


class _FakeResponse:
    def __init__(self, payload: dict):
        self._payload = payload
        self.status_code = 200

    def json(self) -> dict:
        return self._payload

    def raise_for_status(self) -> None:
        pass


class _FakeFarasaClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def post(self, url: str, json: dict) -> _FakeResponse:
        return _FakeResponse(
            {
                "tokens": [
                    {"surface_form": "قَالَ", "dep_label": "Subj", "head": 0},
                    {"surface_form": "الْكِتَابَ", "dep_label": "Obj", "head": 1},
                    {"surface_form": "غَيْرُ", "dep_label": "gen", "head": 2},
                ]
            }
        )


class _UnreachableFarasaClient(_FakeFarasaClient):
    async def post(self, url: str, json: dict) -> _FakeResponse:
        raise httpx.ConnectError("connection refused")


class _ReadErrorFarasaClient(_FakeFarasaClient):
    async def post(self, url: str, json: dict) -> _FakeResponse:
        raise httpx.ReadError("connection dropped mid-response")


class _MalformedFarasaClient(_FakeFarasaClient):
    async def post(self, url: str, json: dict) -> _FakeResponse:
        return _FakeResponse({})


class _EmptyTokensFarasaClient(_FakeFarasaClient):
    async def post(self, url: str, json: dict) -> _FakeResponse:
        return _FakeResponse({"tokens": []})


async def _add_annotated_verse(
    db_session, *, ayah: int, uthmani: str, imlaei: str, word_uthmani: str, word_imlaei: str
) -> None:
    verse = Verse(
        surah_id=1,
        ayah_number=ayah,
        text_uthmani=uthmani,
        text_imlaei=imlaei,
        translation_en="synthetic test verse",
        juz_number=1,
        hizb_number=1,
        page_number=1,
    )
    db_session.add(verse)
    await db_session.flush()
    word = Word(
        verse_id=verse.id,
        position=1,
        text_uthmani=word_uthmani,
        text_imlaei=word_imlaei,
        root="سلم",
        lemma="سَلَام",
        pos_tag="N",
    )
    db_session.add(word)
    await db_session.flush()
    db_session.add(
        NahwAnnotation(
            verse_id=verse.id,
            word_id=word.id,
            token_index=1,
            role="مبتدأ",
            dep_type="SBJ",
            head_index=-1,
            irab="مرفوع",
            sentence_index=1,
        )
    )
    await db_session.commit()


@pytest.mark.asyncio
async def test_parse_exact_corpus_match(client: AsyncClient, seed_quran_data, db_session, monkeypatch):
    db_session.add(NahwAnnotation(verse_id=1, word_id=1, token_index=1, role="فاعل", dep_type="Subj", head_index=2, irab="رفع"))
    await db_session.commit()

    monkeypatch.setattr(httpx, "AsyncClient", _UnreachableFarasaClient)

    verse_text = (await db_session.execute(select(Verse.text_uthmani).where(Verse.id == 1))).scalar_one()
    response = await client.post(
        "/api/v1/nahw/parse",
        json={"text": verse_text, "is_quranic": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "corpus"
    assert data["tokens"][0]["role_key"] == "subject"


@pytest.mark.asyncio
async def test_parse_farasa_path(client: AsyncClient, seed_quran_data, monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", _FakeFarasaClient)

    response = await client.post(
        "/api/v1/nahw/parse",
        json={"text": "جملة غير موجودة في القران", "is_quranic": False},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "farasa"
    assert len(data["tokens"]) == 3
    assert data["tokens"][0]["role_key"] == "subject"
    assert data["tokens"][1]["role_key"] == "object"
    assert data["tokens"][2]["role_key"] == "other"


@pytest.mark.asyncio
async def test_parse_farasa_unreachable_503(client: AsyncClient, seed_quran_data, monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", _UnreachableFarasaClient)

    response = await client.post(
        "/api/v1/nahw/parse",
        json={"text": "جملة غير موجودة في القران", "is_quranic": False},
    )
    assert response.status_code == 503
    assert "unreachable" in response.json()["detail"]


@pytest.mark.asyncio
async def test_verse_lookup_still_works_after_parse(client: AsyncClient, seed_quran_data, db_session, monkeypatch):
    db_session.add(NahwAnnotation(verse_id=1, word_id=1, token_index=1, role="فاعل", dep_type="Subj", head_index=2, irab="رفع"))
    await db_session.commit()
    monkeypatch.setattr(httpx, "AsyncClient", _UnreachableFarasaClient)

    response = await client.get("/api/v1/nahw/verse/1/1")
    assert response.status_code == 200
    assert response.json()["tokens"][0]["role_key"] == "subject"


@pytest.mark.asyncio
async def test_parse_normalizes_arabic_to_imlaei_corpus_match(
    client: AsyncClient, seed_quran_data, db_session, monkeypatch
):
    await _add_annotated_verse(
        db_session,
        ayah=3,
        uthmani="سَلَامٌ عَلَيْكُمْ",
        imlaei="سَلَامٌ عَلَيْكُمْ",
        word_uthmani="سَلَامٌ",
        word_imlaei="سَلَامٌ",
    )
    monkeypatch.setattr(httpx, "AsyncClient", _UnreachableFarasaClient)

    response = await client.post(
        "/api/v1/nahw/parse",
        json={"text": "سلام عليكم", "is_quranic": False},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "corpus"
    assert len(data["tokens"]) == 1
    assert data["tokens"][0]["text_uthmani"] == "سَلَامٌ"


@pytest.mark.asyncio
async def test_parse_repeated_verse_text_returns_409_not_500(
    client: AsyncClient, seed_quran_data, db_session, monkeypatch
):
    verse_text = (
        await db_session.execute(select(Verse.text_uthmani).where(Verse.id == 1))
    ).scalar_one()
    db_session.add(
        Verse(
            surah_id=1,
            ayah_number=3,
            text_uthmani=verse_text,
            text_imlaei=verse_text,
            juz_number=1,
            hizb_number=1,
            page_number=1,
        )
    )
    await db_session.commit()
    monkeypatch.setattr(httpx, "AsyncClient", _UnreachableFarasaClient)

    response = await client.post("/api/v1/nahw/parse", json={"text": verse_text})

    assert response.status_code == 409
    detail = response.json()["detail"]
    assert "1:1" in detail
    assert "1:3" in detail


@pytest.mark.asyncio
async def test_parse_claimed_quranic_text_missing_from_corpus_returns_404(
    client: AsyncClient, seed_quran_data, monkeypatch
):
    monkeypatch.setattr(httpx, "AsyncClient", _FakeFarasaClient)

    response = await client.post(
        "/api/v1/nahw/parse",
        json={"text": "جملة غير موجودة في القران", "is_quranic": True},
    )

    assert response.status_code == 404
    assert "not found in the corpus" in response.json()["detail"]


@pytest.mark.asyncio
async def test_parse_farasa_read_error_returns_503(client: AsyncClient, seed_quran_data, monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", _ReadErrorFarasaClient)

    response = await client.post(
        "/api/v1/nahw/parse",
        json={"text": "جملة غير موجودة في القران"},
    )

    assert response.status_code == 503
    assert "unreachable" in response.json()["detail"]


@pytest.mark.asyncio
async def test_parse_farasa_malformed_payload_returns_502(
    client: AsyncClient, seed_quran_data, monkeypatch
):
    monkeypatch.setattr(httpx, "AsyncClient", _MalformedFarasaClient)

    response = await client.post(
        "/api/v1/nahw/parse",
        json={"text": "جملة غير موجودة في القران"},
    )

    assert response.status_code == 502
    assert "malformed" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_parse_farasa_empty_tokens_returns_502(
    client: AsyncClient, seed_quran_data, monkeypatch
):
    monkeypatch.setattr(httpx, "AsyncClient", _EmptyTokensFarasaClient)

    response = await client.post(
        "/api/v1/nahw/parse",
        json={"text": "جملة غير موجودة في القران"},
    )

    assert response.status_code == 502
    assert "malformed" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_parse_rejects_empty_text(client: AsyncClient, seed_quran_data):
    response = await client.post("/api/v1/nahw/parse", json={"text": ""})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_parse_rejects_missing_text(client: AsyncClient, seed_quran_data):
    response = await client.post("/api/v1/nahw/parse", json={"is_quranic": False})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_parse_rejects_oversized_text(client: AsyncClient, seed_quran_data):
    response = await client.post("/api/v1/nahw/parse", json={"text": "ا" * 5001})
    assert response.status_code == 422
