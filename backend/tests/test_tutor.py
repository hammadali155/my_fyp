from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.main import app
from app.models.chat import ChatMessage, ChatSession
from app.models.quran import Surah, Verse
from app.services.llm_client import ChatMessage as LLMChatMessage
from app.services.llm_client import (
    LLMError,
    LLMNotConfiguredError,
    get_llm_client,
)
from app.services.tutor_prompts import TUTOR_SYSTEM_PROMPT
from app.services.tutor_service import select_history
from tests.fake_llm import FakeLLMClient


def _use_llm(fake: FakeLLMClient) -> None:
    app.dependency_overrides[get_llm_client] = lambda: fake


async def _second_user_headers(client: AsyncClient) -> dict[str, str]:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "second@example.com",
            "name": "Second Learner",
            "password": "SecurePassword123!",
        },
    )
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['tokens']['access_token']}"}


async def _seeded_verse(db_session: AsyncSession, ayah_number: int) -> Verse:
    return (
        await db_session.execute(
            select(Verse).where(Verse.surah_id == 1, Verse.ayah_number == ayah_number)
        )
    ).scalar_one()


async def _all_messages(db_session: AsyncSession) -> list[ChatMessage]:
    return list(
        (
            await db_session.execute(select(ChatMessage).order_by(ChatMessage.id.asc()))
        )
        .scalars()
        .all()
    )


async def _assert_citations_exist(
    db_session: AsyncSession, citations: list[dict[str, int]]
) -> None:
    for citation in citations:
        row = (
            await db_session.execute(
                select(Verse.id)
                .join(Surah, Verse.surah_id == Surah.id)
                .where(
                    Surah.number == citation["surah"],
                    Verse.ayah_number == citation["ayah"],
                )
            )
        ).first()
        assert row is not None, citation


async def test_chat_success_stores_messages_and_returns_citations(
    client: AsyncClient,
    auth_headers,
    registered_user,
    seed_quran_data,
    db_session: AsyncSession,
) -> None:
    verse = await _seeded_verse(db_session, 2)
    fake = FakeLLMClient(reply="ٱلْحَمْدُ is a noun. Compare 1:2.")
    _use_llm(fake)

    response = await client.post(
        "/api/v1/tutor/chat",
        json={"message": "What does 1:2 mean?"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["session_id"], int)
    assert data["reply"] == "ٱلْحَمْدُ is a noun. Compare 1:2."
    assert data["citations"] == [{"surah": 1, "ayah": 2}]
    assert data["usage"] == {"prompt_tokens": 12, "completion_tokens": 6}
    assert data["model"] == get_settings().gemini_model
    assert data["truncated_context"] is False
    assert data["incomplete"] is False
    await _assert_citations_exist(db_session, data["citations"])

    assert len(fake.calls) == 1
    assert fake.calls[0].system_prompt == TUTOR_SYSTEM_PROMPT.format(
        level="beginner", language="English"
    )
    prompt = fake.prompts[0]
    assert verse.text_uthmani in prompt
    assert "What does 1:2 mean?" in prompt
    assert "1:2" in prompt

    messages = await _all_messages(db_session)
    assert [message.role for message in messages] == ["user", "assistant"]
    assert messages[0].content == "What does 1:2 mean?"
    assert messages[0].retrieved_verse_ids == [verse.id]
    assert messages[1].content == "ٱلْحَمْدُ is a noun. Compare 1:2."
    assert messages[1].citations_json == [{"surah": 1, "ayah": 2}]
    assert messages[1].retrieved_verse_ids == [verse.id]
    assert messages[1].prompt_tokens == 12
    assert messages[1].completion_tokens == 6
    assert messages[1].model == get_settings().gemini_model

    session = (
        await db_session.execute(
            select(ChatSession).where(ChatSession.id == data["session_id"])
        )
    ).scalar_one()
    assert session.id == data["session_id"]
    assert session.user_id == registered_user["user"]["id"]
    assert messages[0].session_id == data["session_id"]


async def test_chat_reuses_session_and_sends_history(
    client: AsyncClient, auth_headers, seed_quran_data, db_session: AsyncSession
) -> None:
    fake = FakeLLMClient(reply="First answer.")
    _use_llm(fake)

    first = await client.post(
        "/api/v1/tutor/chat",
        json={"message": "What does 1:2 mean?"},
        headers=auth_headers,
    )
    assert first.status_code == 200
    session_id = first.json()["session_id"]

    fake.reply = "Second answer."
    second = await client.post(
        "/api/v1/tutor/chat",
        json={"message": "Give me another example", "session_id": session_id},
        headers=auth_headers,
    )

    assert second.status_code == 200
    assert second.json()["session_id"] == session_id
    assert len(fake.calls) == 2
    history = fake.calls[1].messages
    assert [message.role for message in history] == ["user", "assistant", "user"]
    assert history[0].content == "What does 1:2 mean?"
    assert history[1].content == "First answer."
    assert "Retrieved context" in history[2].content
    assert "Give me another example" in history[2].content

    sessions = (
        (await db_session.execute(select(ChatSession))).scalars().all()
    )
    assert len(sessions) == 1


async def test_chat_requires_authentication(
    client: AsyncClient, seed_quran_data
) -> None:
    response = await client.post(
        "/api/v1/tutor/chat", json={"message": "What does 1:2 mean?"}
    )
    assert response.status_code == 401


async def test_chat_rejects_another_users_session(
    client: AsyncClient, auth_headers, seed_quran_data, db_session: AsyncSession
) -> None:
    _use_llm(FakeLLMClient(reply="See 1:2."))
    created = await client.post(
        "/api/v1/tutor/chat",
        json={"message": "What does 1:2 mean?"},
        headers=auth_headers,
    )
    assert created.status_code == 200
    session_id = created.json()["session_id"]

    other = await _second_user_headers(client)

    response = await client.post(
        "/api/v1/tutor/chat",
        json={"message": "What about this verse?", "session_id": session_id},
        headers=other,
    )

    assert response.status_code == 404
    assert (await _all_messages(db_session))[-1].content == "See 1:2."

    listed = await client.get("/api/v1/tutor/sessions", headers=other)
    assert listed.status_code == 200
    assert listed.json()["sessions"] == []

    deleted = await client.delete(
        f"/api/v1/tutor/sessions/{session_id}", headers=other
    )
    assert deleted.status_code == 404


async def test_chat_enforces_daily_limit_before_anything_else(
    client: AsyncClient,
    auth_headers,
    seed_quran_data,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(get_settings(), "tutor_daily_message_limit", 1)
    fake = FakeLLMClient(reply="See 1:2.")
    _use_llm(fake)

    first = await client.post(
        "/api/v1/tutor/chat",
        json={"message": "What does 1:2 mean?"},
        headers=auth_headers,
    )
    assert first.status_code == 200

    second = await client.post(
        "/api/v1/tutor/chat",
        json={"message": "And again?", "session_id": first.json()["session_id"]},
        headers=auth_headers,
    )

    assert second.status_code == 429
    assert "Daily tutor message limit" in second.json()["detail"]
    assert len(fake.calls) == 1
    assert len(await _all_messages(db_session)) == 2


async def test_chat_returns_503_when_model_fails(
    client: AsyncClient, auth_headers, seed_quran_data, db_session: AsyncSession
) -> None:
    _use_llm(FakeLLMClient(error=LLMError("upstream failed")))

    response = await client.post(
        "/api/v1/tutor/chat",
        json={"message": "What does 1:2 mean?"},
        headers=auth_headers,
    )

    assert response.status_code == 503
    assert "unavailable" in response.json()["detail"].lower()
    assert await _all_messages(db_session) == []
    sessions = (await db_session.execute(select(ChatSession))).scalars().all()
    assert len(sessions) == 0


async def test_chat_returns_503_when_not_configured(
    client: AsyncClient, auth_headers, seed_quran_data
) -> None:
    _use_llm(FakeLLMClient(error=LLMNotConfiguredError("GEMINI_API_KEY is missing")))

    response = await client.post(
        "/api/v1/tutor/chat",
        json={"message": "What does 1:2 mean?"},
        headers=auth_headers,
    )

    assert response.status_code == 503
    assert "not configured" in response.json()["detail"].lower()


async def test_chat_rejects_too_long_message(
    client: AsyncClient, auth_headers, seed_quran_data, db_session: AsyncSession
) -> None:
    fake = FakeLLMClient()
    _use_llm(fake)

    response = await client.post(
        "/api/v1/tutor/chat",
        json={"message": "x" * 2001},
        headers=auth_headers,
    )

    assert response.status_code == 422
    assert fake.calls == []
    assert await _all_messages(db_session) == []


async def test_chat_drops_references_not_in_context(
    client: AsyncClient, auth_headers, seed_quran_data, db_session: AsyncSession
) -> None:
    fake = FakeLLMClient(reply="The rule appears in 1:1, 1:2 and also 2:255.")
    _use_llm(fake)

    response = await client.post(
        "/api/v1/tutor/chat",
        json={"message": "What does 1:2 mean?"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    citations = response.json()["citations"]
    assert citations == [{"surah": 1, "ayah": 2}]
    await _assert_citations_exist(db_session, citations)

    assistant = (await _all_messages(db_session))[-1]
    assert assistant.citations_json == [{"surah": 1, "ayah": 2}]


async def test_chat_returns_no_citations_when_every_reference_is_unknown(
    client: AsyncClient, auth_headers, seed_quran_data, db_session: AsyncSession
) -> None:
    _use_llm(FakeLLMClient(reply="As Allah says in 2:255, He is the Ever-Living."))

    response = await client.post(
        "/api/v1/tutor/chat",
        json={"message": "Explain 1:2"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["citations"] == []


async def test_chat_uses_request_reference(
    client: AsyncClient, auth_headers, seed_quran_data, db_session: AsyncSession
) -> None:
    verse = await _seeded_verse(db_session, 1)
    fake = FakeLLMClient(reply="It opens with 1:1.")
    _use_llm(fake)

    response = await client.post(
        "/api/v1/tutor/chat",
        json={
            "message": "Explain this verse",
            "reference": {"surah_number": 1, "ayah_number": 1},
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["citations"] == [{"surah": 1, "ayah": 1}]
    assert verse.text_uthmani in fake.prompts[0]


async def test_sessions_list_and_delete(
    client: AsyncClient, auth_headers, seed_quran_data, db_session: AsyncSession
) -> None:
    _use_llm(FakeLLMClient(reply="See 1:2."))
    created = await client.post(
        "/api/v1/tutor/chat",
        json={"message": "What does 1:2 mean?"},
        headers=auth_headers,
    )
    session_id = created.json()["session_id"]

    listed = await client.get("/api/v1/tutor/sessions", headers=auth_headers)
    assert listed.status_code == 200
    sessions = listed.json()["sessions"]
    assert [session["id"] for session in sessions] == [session_id]
    assert sessions[0]["title"] == "New session"
    assert sessions[0]["message_count"] == 2

    deleted = await client.delete(
        f"/api/v1/tutor/sessions/{session_id}", headers=auth_headers
    )
    assert deleted.status_code == 204

    empty = await client.get("/api/v1/tutor/sessions", headers=auth_headers)
    assert empty.json()["sessions"] == []
    assert await _all_messages(db_session) == []

    missing = await client.delete(
        f"/api/v1/tutor/sessions/{session_id}", headers=auth_headers
    )
    assert missing.status_code == 404


def test_select_history_keeps_the_most_recent_messages_within_budget() -> None:
    messages = [
        LLMChatMessage(role="user", content="x" * 400),
        LLMChatMessage(role="assistant", content="y" * 400),
        LLMChatMessage(role="user", content="recent"),
    ]

    assert select_history(messages, max_tokens=20) == [messages[2]]
    assert select_history(messages, max_tokens=120) == messages[1:]
    assert select_history(messages, max_tokens=400) == messages


def test_select_history_always_keeps_the_newest_message() -> None:
    messages = [LLMChatMessage(role="user", content="z" * 4000)]

    assert select_history(messages, max_tokens=0) == messages
