from __future__ import annotations

from collections.abc import Sequence

import pytest

from app.services.llm_client import (
    ChatMessage,
    GeminiLLMClient,
    GenerationSettings,
    LLMClient,
    LLMError,
    LLMNotConfiguredError,
    LLMResult,
    LLMStreamEvent,
    LLMTransientError,
    _retry_delay,
    get_llm_client,
)
from tests.fake_llm import FakeLLMClient


class GenerateOnlyClient(LLMClient):
    async def generate(
        self,
        *,
        system_prompt: str,
        messages: Sequence[ChatMessage],
        settings: GenerationSettings | None = None,
    ) -> LLMResult:
        return LLMResult(text="whole reply", prompt_tokens=7, completion_tokens=3)


class ScriptedGeminiClient(GeminiLLMClient):
    """Gemini client whose single API call is scripted by the test."""

    def __init__(
        self,
        outcomes: list[LLMResult | Exception],
        *,
        max_retries: int = 0,
    ) -> None:
        super().__init__(
            api_key="test-key",
            max_retries=max_retries,
            retry_backoff_seconds=0.0,
        )
        self.outcomes = outcomes
        self.calls = 0
        self.seen_settings: GenerationSettings | None = None

    async def _call_model(
        self,
        *,
        system_prompt: str,
        messages: Sequence[ChatMessage],
        settings: GenerationSettings,
    ) -> LLMResult:
        self.seen_settings = settings
        outcome = self.outcomes[min(self.calls, len(self.outcomes) - 1)]
        self.calls += 1
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def _messages() -> list[ChatMessage]:
    return [ChatMessage(role="user", content="What is a root?")]


def test_llm_client_is_abstract() -> None:
    with pytest.raises(TypeError):
        LLMClient()  # type: ignore[abstract]


def test_retry_delay_is_exponential() -> None:
    assert _retry_delay(0, 0.5) == 0.5
    assert _retry_delay(1, 0.5) == 1.0
    assert _retry_delay(2, 0.5) == 2.0


@pytest.mark.asyncio
async def test_fake_client_returns_scripted_reply_and_records_the_call() -> None:
    fake = FakeLLMClient(reply="scripted", prompt_tokens=4, completion_tokens=2)

    result = await fake.generate(
        system_prompt="you are a tutor",
        messages=_messages(),
    )

    assert result == LLMResult(text="scripted", prompt_tokens=4, completion_tokens=2)
    assert len(fake.calls) == 1
    assert fake.calls[0].system_prompt == "you are a tutor"
    assert fake.calls[0].messages == _messages()
    assert fake.calls[0].settings == GenerationSettings()


@pytest.mark.asyncio
async def test_fake_client_raises_its_scripted_error() -> None:
    fake = FakeLLMClient(error=LLMNotConfiguredError("no key"))

    with pytest.raises(LLMNotConfiguredError):
        await fake.generate(system_prompt="s", messages=_messages())

    assert len(fake.calls) == 1


@pytest.mark.asyncio
async def test_gemini_client_requires_api_key() -> None:
    client = GeminiLLMClient(api_key="")

    with pytest.raises(LLMNotConfiguredError):
        await client.generate(system_prompt="s", messages=_messages())


@pytest.mark.asyncio
async def test_gemini_client_returns_text_and_token_counts() -> None:
    expected = LLMResult(text="answer", prompt_tokens=9, completion_tokens=3)
    client = ScriptedGeminiClient([expected])

    result = await client.generate(system_prompt="s", messages=_messages())

    assert result == expected
    assert client.calls == 1


@pytest.mark.asyncio
async def test_gemini_client_retries_transient_errors_then_succeeds() -> None:
    client = ScriptedGeminiClient(
        [LLMTransientError("429"), LLMResult(text="answer")],
        max_retries=1,
    )

    result = await client.generate(system_prompt="s", messages=_messages())

    assert result.text == "answer"
    assert client.calls == 2


@pytest.mark.asyncio
async def test_gemini_client_gives_up_after_max_retries() -> None:
    client = ScriptedGeminiClient([LLMTransientError("503")], max_retries=2)

    with pytest.raises(LLMError) as excinfo:
        await client.generate(system_prompt="s", messages=_messages())

    assert not isinstance(excinfo.value, LLMNotConfiguredError)
    assert client.calls == 3


@pytest.mark.asyncio
async def test_gemini_client_does_not_retry_permanent_errors() -> None:
    client = ScriptedGeminiClient([LLMError("400 bad request")], max_retries=2)

    with pytest.raises(LLMError):
        await client.generate(system_prompt="s", messages=_messages())

    assert client.calls == 1


@pytest.mark.asyncio
async def test_gemini_client_defaults_generation_settings() -> None:
    client = ScriptedGeminiClient([LLMResult(text="answer")])

    await client.generate(system_prompt="s", messages=_messages())

    assert client.seen_settings == GenerationSettings()


@pytest.mark.asyncio
async def test_gemini_client_forwards_explicit_generation_settings() -> None:
    settings = GenerationSettings(temperature=0.1, max_output_tokens=64, json_output=True)
    client = ScriptedGeminiClient([LLMResult(text="answer")])

    await client.generate(system_prompt="s", messages=_messages(), settings=settings)

    assert client.seen_settings == settings


@pytest.mark.asyncio
async def test_stream_falls_back_to_one_generate_event() -> None:
    client = GenerateOnlyClient()

    events = [
        event
        async for event in client.stream(
            system_prompt="s", messages=_messages()
        )
    ]

    assert events == [LLMStreamEvent(text="whole reply", prompt_tokens=7, completion_tokens=3)]


def test_get_llm_client_builds_the_gemini_implementation() -> None:
    assert isinstance(get_llm_client(), GeminiLLMClient)
