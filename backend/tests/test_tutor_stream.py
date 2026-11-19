from __future__ import annotations

import json

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.main import app
from app.models.chat import ChatMessage
from app.services.llm_client import LLMError, get_llm_client
from tests.fake_llm import FakeLLMClient

STREAM_URL = "/api/v1/tutor/chat/stream"


def _use_llm(fake: FakeLLMClient) -> None:
    app.dependency_overrides[get_llm_client] = lambda: fake


def _parse_sse(raw: str) -> list[tuple[str, dict]]:
    events: list[tuple[str, dict]] = []
    for block in raw.split("\n\n"):
        if not block.strip():
            continue
        name = "message"
        data_lines: list[str] = []
        for line in block.splitlines():
            if line.startswith("event:"):
                name = line.removeprefix("event:").strip()
            elif line.startswith("data:"):
                data_lines.append(line.removeprefix("data:").strip())
        events.append((name, json.loads("\n".join(data_lines))))
    return events


async def _stream(
    client: AsyncClient, headers: dict[str, str], payload: dict
) -> tuple[int, dict[str, str], list[tuple[str, dict]]]:
    async with client.stream("POST", STREAM_URL, json=payload, headers=headers) as response:
        raw = "".join([chunk async for chunk in response.aiter_text()])
        return response.status_code, dict(response.headers), _parse_sse(raw)


async def _all_messages(db_session: AsyncSession) -> list[ChatMessage]:
    return list(
        (
            await db_session.execute(select(ChatMessage).order_by(ChatMessage.id.asc()))
        )
        .scalars()
        .all()
    )


async def _second_user_headers(client: AsyncClient) -> dict[str, str]:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "stream-second@example.com",
            "name": "Second Learner",
            "password": "SecurePassword123!",
        },
    )
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['tokens']['access_token']}"}


async def test_stream_delivers_tokens_and_stores_complete_message(
    client: AsyncClient, auth_headers, seed_quran_data, db_session: AsyncSession
) -> None:
    fake = FakeLLMClient(stream_chunks=["ٱلْحَمْدُ ", "is a noun. ", "See 1:2."])
    _use_llm(fake)

    status_code, headers, events = await _stream(
        client, auth_headers, {"message": "What does 1:2 mean?"}
    )

    assert status_code == 200
    assert headers["content-type"].startswith("text/event-stream")
    assert [name for name, _ in events] == ["token", "token", "token", "done"]
    streamed = "".join(data["text"] for name, data in events if name == "token")
    assert streamed == "ٱلْحَمْدُ is a noun. See 1:2."

    done = events[-1][1]
    assert done["reply"] == streamed
    assert done["citations"] == [{"surah": 1, "ayah": 2}]
    assert done["incomplete"] is False
    assert done["usage"] == {"prompt_tokens": 12, "completion_tokens": 6}
    assert done["model"] == get_settings().gemini_model

    messages = await _all_messages(db_session)
    assert [message.role for message in messages] == ["user", "assistant"]
    assert messages[0].content == "What does 1:2 mean?"
    assert messages[1].content == streamed
    assert messages[1].citations_json == [{"surah": 1, "ayah": 2}]
    assert messages[1].prompt_tokens == 12
    assert messages[1].completion_tokens == 6
    assert messages[1].incomplete is False

    assert len(fake.stream_calls) == 1
    assert "Retrieved context" in fake.stream_calls[0].messages[-1].content


async def test_stream_stores_partial_message_and_flags_it_incomplete(
    client: AsyncClient, auth_headers, seed_quran_data, db_session: AsyncSession
) -> None:
    fake = FakeLLMClient(
        stream_chunks=["The word is "],
        stream_error=LLMError("upstream broke"),
        stream_error_after=1,
    )
    _use_llm(fake)

    status_code, _, events = await _stream(
        client, auth_headers, {"message": "What does 1:2 mean?"}
    )

    assert status_code == 200
    assert [name for name, _ in events] == ["token", "error"]
    assert events[0][1] == {"text": "The word is "}
    assert "unavailable" in events[1][1]["detail"].lower()
    assert events[1][1]["incomplete"] is True

    messages = await _all_messages(db_session)
    assert [message.role for message in messages] == ["user", "assistant"]
    assert messages[1].content == "The word is "
    assert messages[1].incomplete is True
    assert messages[1].citations_json == []
    assert messages[1].prompt_tokens is None
    assert messages[1].completion_tokens is None


async def test_stream_stores_empty_partial_when_model_fails_before_first_token(
    client: AsyncClient, auth_headers, seed_quran_data, db_session: AsyncSession
) -> None:
    _use_llm(FakeLLMClient(stream_error=LLMError("no connection")))

    status_code, _, events = await _stream(
        client, auth_headers, {"message": "What does 1:2 mean?"}
    )

    assert status_code == 200
    assert [name for name, _ in events] == ["error"]
    messages = await _all_messages(db_session)
    assert messages[-1].role == "assistant"
    assert messages[-1].content == ""
    assert messages[-1].incomplete is True


async def test_stream_drops_references_not_in_context(
    client: AsyncClient, auth_headers, seed_quran_data
) -> None:
    _use_llm(FakeLLMClient(stream_chunks=["Compare 1:2 with 2:255."]))

    status_code, _, events = await _stream(
        client, auth_headers, {"message": "What does 1:2 mean?"}
    )

    assert status_code == 200
    assert events[-1][1]["citations"] == [{"surah": 1, "ayah": 2}]


async def test_stream_enforces_daily_limit_before_streaming(
    client: AsyncClient,
    auth_headers,
    seed_quran_data,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(get_settings(), "tutor_daily_message_limit", 0)
    fake = FakeLLMClient()
    _use_llm(fake)

    response = await client.post(
        STREAM_URL, json={"message": "What does 1:2 mean?"}, headers=auth_headers
    )

    assert response.status_code == 429
    assert "Daily tutor message limit" in response.json()["detail"]
    assert fake.stream_calls == []


async def test_stream_rejects_another_users_session(
    client: AsyncClient, auth_headers, seed_quran_data
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
        STREAM_URL,
        json={"message": "And this?", "session_id": session_id},
        headers=other,
    )

    assert response.status_code == 404


async def test_stream_requires_authentication(client: AsyncClient, seed_quran_data) -> None:
    response = await client.post(STREAM_URL, json={"message": "What does 1:2 mean?"})
    assert response.status_code == 401


async def test_stream_rejects_too_long_message(
    client: AsyncClient, auth_headers, seed_quran_data
) -> None:
    fake = FakeLLMClient()
    _use_llm(fake)

    response = await client.post(
        STREAM_URL, json={"message": "x" * 2001}, headers=auth_headers
    )

    assert response.status_code == 422
    assert fake.stream_calls == []
