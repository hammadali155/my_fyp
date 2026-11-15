from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.main import app
from app.models.quran import NahwAnnotation
from app.models.user import User
from app.services.gemini_client import GeminiError, GeminiNotConfiguredError, get_gemini_client
from app.services.nahw_explain_service import clear_explanation_cache


class FakeGeminiClient:
    def __init__(self, reply: str = "grounded explanation", error: Exception | None = None) -> None:
        self.reply = reply
        self.error = error
        self.prompts: list[str] = []

    async def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        if self.error is not None:
            raise self.error
        return self.reply


@pytest.fixture(autouse=True)
def _reset_cache():
    clear_explanation_cache()
    yield
    clear_explanation_cache()


def _use_gemini(fake: FakeGeminiClient) -> None:
    app.dependency_overrides[get_gemini_client] = lambda: fake


async def _add_annotation(db_session) -> None:
    db_session.add(
        NahwAnnotation(
            verse_id=1,
            word_id=1,
            token_index=1,
            role="مجرور",
            dep_type="gen",
            head_index=-1,
            irab="مجرور",
            sentence_index=1,
        )
    )
    await db_session.commit()


@pytest.mark.asyncio
async def test_explain_word_returns_grounded_data(
    client: AsyncClient, auth_headers, seed_quran_data, db_session
):
    await _add_annotation(db_session)
    fake = FakeGeminiClient(reply="The word is governed by the preposition.")
    _use_gemini(fake)

    response = await client.get("/api/v1/nahw/explain/1", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["word_id"] == 1
    assert data["language"] == "en"
    assert data["source"] == "gemini"
    assert data["cached"] is False
    assert data["explanation"] == "The word is governed by the preposition."
    grounding = data["grounding"]
    assert grounding["word_id"] == 1
    assert grounding["position"] == 1
    assert grounding["surah_number"] == 1
    assert grounding["ayah_number"] == 1
    assert grounding["verse_text"] == "بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ"
    assert grounding["morphology"]["root"] == "سمو"
    assert grounding["morphology"]["lemma"] == "اسْم"
    assert grounding["relation"]["role"] == "مجرور"
    assert grounding["relation"]["dep_type"] == "gen"
    assert len(fake.prompts) == 1


@pytest.mark.asyncio
async def test_explain_word_prompt_contains_only_stored_data_and_rules(
    client: AsyncClient, auth_headers, seed_quran_data, db_session
):
    await _add_annotation(db_session)
    fake = FakeGeminiClient()
    _use_gemini(fake)

    response = await client.get("/api/v1/nahw/explain/1", headers=auth_headers)

    assert response.status_code == 200
    prompt = fake.prompts[0]
    assert "بِسْمِ" in prompt
    assert "مجرور" in prompt
    assert "Use ONLY" in prompt
    assert "Do not" in prompt
    assert "null" in prompt
    assert "neither is a word position" in prompt
    assert "English" in prompt


@pytest.mark.asyncio
async def test_explain_word_reports_head_verse_for_cross_verse_head(
    client: AsyncClient, auth_headers, seed_quran_data, db_session
):
    db_session.add(
        NahwAnnotation(
            verse_id=1,
            word_id=1,
            token_index=1,
            role="مضاف إليه",
            dep_type="Poss",
            head_index=2,
            head_surah_number=1,
            head_ayah_number=2,
            irab="مجرور",
            sentence_index=1,
        )
    )
    await db_session.commit()
    fake = FakeGeminiClient()
    _use_gemini(fake)

    response = await client.get("/api/v1/nahw/explain/1", headers=auth_headers)

    assert response.status_code == 200
    relation = response.json()["grounding"]["relation"]
    assert relation["head_index"] == 2
    assert relation["head_surah_number"] == 1
    assert relation["head_ayah_number"] == 2
    assert '"head_ayah_number": 2' in fake.prompts[0]


@pytest.mark.asyncio
async def test_explain_word_is_cached_by_word_and_language(
    client: AsyncClient, auth_headers, seed_quran_data, db_session
):
    await _add_annotation(db_session)
    fake = FakeGeminiClient()
    _use_gemini(fake)

    first = await client.get("/api/v1/nahw/explain/1", headers=auth_headers)
    second = await client.get("/api/v1/nahw/explain/1", headers=auth_headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["cached"] is False
    assert second.json()["cached"] is True
    assert len(fake.prompts) == 1


@pytest.mark.asyncio
async def test_explain_word_cache_key_includes_language(
    client: AsyncClient, auth_headers, seed_quran_data, db_session
):
    await _add_annotation(db_session)
    fake = FakeGeminiClient()
    _use_gemini(fake)

    first = await client.get("/api/v1/nahw/explain/1", headers=auth_headers)
    user = (
        await db_session.execute(select(User).where(User.email == "talib@example.com"))
    ).scalar_one()
    user.ui_lang = "ur"
    await db_session.commit()

    second = await client.get("/api/v1/nahw/explain/1", headers=auth_headers)

    assert first.json()["language"] == "en"
    assert second.json()["language"] == "ur"
    assert second.json()["cached"] is False
    assert "Urdu" in fake.prompts[1]
    assert len(fake.prompts) == 2


@pytest.mark.asyncio
async def test_explain_word_without_treebank_marks_missing_relation(
    client: AsyncClient, auth_headers, seed_quran_data
):
    fake = FakeGeminiClient()
    _use_gemini(fake)

    response = await client.get("/api/v1/nahw/explain/2", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["grounding"]["relation"] is None
    assert "treebank_relation" in data["grounding"]["missing_data"]
    assert len(fake.prompts) == 1


@pytest.mark.asyncio
async def test_explain_word_requires_authentication(client: AsyncClient, seed_quran_data):
    response = await client.get("/api/v1/nahw/explain/1")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_explain_word_unknown_id_returns_404(
    client: AsyncClient, auth_headers, seed_quran_data
):
    fake = FakeGeminiClient()
    _use_gemini(fake)

    response = await client.get("/api/v1/nahw/explain/999", headers=auth_headers)

    assert response.status_code == 404
    assert not fake.prompts


@pytest.mark.asyncio
async def test_explain_word_rejects_non_integer_id(
    client: AsyncClient, auth_headers, seed_quran_data
):
    response = await client.get("/api/v1/nahw/explain/not-a-number", headers=auth_headers)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_explain_word_returns_503_when_gemini_not_configured(
    client: AsyncClient, auth_headers, seed_quran_data, db_session
):
    await _add_annotation(db_session)
    _use_gemini(FakeGeminiClient(error=GeminiNotConfiguredError("GEMINI_API_KEY is missing")))

    response = await client.get("/api/v1/nahw/explain/1", headers=auth_headers)

    assert response.status_code == 503
    assert "not configured" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_explain_word_returns_503_when_gemini_fails(
    client: AsyncClient, auth_headers, seed_quran_data, db_session
):
    await _add_annotation(db_session)
    _use_gemini(FakeGeminiClient(error=GeminiError("upstream failed")))

    response = await client.get("/api/v1/nahw/explain/1", headers=auth_headers)

    assert response.status_code == 503
    assert "unavailable" in response.json()["detail"].lower()
