from __future__ import annotations

import httpx
import pytest

from app.services.gemini_client import (
    GeminiClient,
    GeminiError,
    GeminiNotConfiguredError,
)

_SUCCESS_BODY = {
    "candidates": [
        {"content": {"parts": [{"text": "grounded explanation"}]}},
    ]
}

_EMPTY_BODY: dict = {"candidates": []}


def _mock_transport(statuses: list[int], body: dict) -> tuple[httpx.MockTransport, dict[str, int]]:
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        index = min(calls["count"], len(statuses) - 1)
        calls["count"] += 1
        return httpx.Response(statuses[index], json=body)

    return httpx.MockTransport(handler), calls


@pytest.mark.asyncio
async def test_generate_raises_when_api_key_missing():
    client = GeminiClient(api_key="")
    with pytest.raises(GeminiNotConfiguredError):
        await client.generate("prompt")


@pytest.mark.asyncio
async def test_generate_returns_text_from_first_successful_response():
    transport, calls = _mock_transport([200], _SUCCESS_BODY)
    client = GeminiClient(api_key="test-key", transport=transport, max_retries=0)
    assert await client.generate("prompt") == "grounded explanation"
    assert calls["count"] == 1


@pytest.mark.asyncio
async def test_generate_retries_on_server_error_then_succeeds():
    transport, calls = _mock_transport([500, 200], _SUCCESS_BODY)
    client = GeminiClient(
        api_key="test-key",
        transport=transport,
        max_retries=1,
        retry_backoff_seconds=0.0,
    )
    assert await client.generate("prompt") == "grounded explanation"
    assert calls["count"] == 2


@pytest.mark.asyncio
async def test_generate_gives_up_after_max_retries():
    transport, calls = _mock_transport([500], _SUCCESS_BODY)
    client = GeminiClient(
        api_key="test-key",
        transport=transport,
        max_retries=2,
        retry_backoff_seconds=0.0,
    )
    with pytest.raises(GeminiError):
        await client.generate("prompt")
    assert calls["count"] == 3


@pytest.mark.asyncio
async def test_generate_does_not_retry_client_errors():
    transport, calls = _mock_transport([400], _SUCCESS_BODY)
    client = GeminiClient(
        api_key="test-key",
        transport=transport,
        max_retries=2,
        retry_backoff_seconds=0.0,
    )
    with pytest.raises(GeminiError):
        await client.generate("prompt")
    assert calls["count"] == 1


@pytest.mark.asyncio
async def test_generate_raises_on_empty_candidates():
    transport, _ = _mock_transport([200], _EMPTY_BODY)
    client = GeminiClient(api_key="test-key", transport=transport, max_retries=0)
    with pytest.raises(GeminiError):
        await client.generate("prompt")
