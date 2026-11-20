from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass
from typing import Annotated, Literal

import httpx
from fastapi import Depends

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("services.llm")

MessageRole = Literal["user", "assistant"]

_GEMINI_ROLES: dict[MessageRole, str] = {"user": "user", "assistant": "model"}


@dataclass(frozen=True)
class ChatMessage:
    role: MessageRole
    content: str


@dataclass(frozen=True)
class GenerationSettings:
    temperature: float = 0.3
    max_output_tokens: int = 512
    json_output: bool = False


@dataclass(frozen=True)
class LLMResult:
    text: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


@dataclass(frozen=True)
class LLMStreamEvent:
    text: str = ""
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


class LLMError(RuntimeError):
    """Base failure for every LLM backend. Routers map it to HTTP 503."""


class LLMNotConfiguredError(LLMError):
    """The backend cannot be used at all (missing API key or SDK)."""


class LLMTransientError(LLMError):
    """A retryable upstream failure: rate limit, 5xx, or transport error."""


class LLMClient(ABC):
    @abstractmethod
    async def generate(
        self,
        *,
        system_prompt: str,
        messages: Sequence[ChatMessage],
        settings: GenerationSettings | None = None,
    ) -> LLMResult:
        """Generate a reply from a system prompt, the conversation and generation settings."""

    async def stream(
        self,
        *,
        system_prompt: str,
        messages: Sequence[ChatMessage],
        settings: GenerationSettings | None = None,
    ) -> AsyncIterator[LLMStreamEvent]:
        """Yield reply chunks; backends without streaming yield the full reply once."""
        result = await self.generate(
            system_prompt=system_prompt,
            messages=messages,
            settings=settings,
        )
        yield LLMStreamEvent(
            text=result.text,
            prompt_tokens=result.prompt_tokens,
            completion_tokens=result.completion_tokens,
        )


def _retry_delay(attempt: int, base_seconds: float) -> float:
    return base_seconds * (2.0**attempt)


class GeminiLLMClient(LLMClient):
    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        timeout_seconds: float | None = None,
        max_retries: int | None = None,
        retry_backoff_seconds: float | None = None,
    ) -> None:
        settings = get_settings()
        self._api_key = settings.gemini_api_key if api_key is None else api_key
        self._model = model or settings.gemini_model
        self._timeout_seconds = (
            settings.gemini_timeout_seconds if timeout_seconds is None else timeout_seconds
        )
        self._max_retries = settings.gemini_max_retries if max_retries is None else max_retries
        self._retry_backoff_seconds = (
            settings.gemini_retry_backoff_seconds
            if retry_backoff_seconds is None
            else retry_backoff_seconds
        )

    async def generate(
        self,
        *,
        system_prompt: str,
        messages: Sequence[ChatMessage],
        settings: GenerationSettings | None = None,
    ) -> LLMResult:
        if not self._api_key:
            raise LLMNotConfiguredError("GEMINI_API_KEY is not set")

        resolved = settings or GenerationSettings()
        last_error: Exception | None = None

        for attempt in range(self._max_retries + 1):
            try:
                return await self._call_model(
                    system_prompt=system_prompt,
                    messages=messages,
                    settings=resolved,
                )
            except LLMTransientError as exc:
                last_error = exc
                logger.warning(
                    "Gemini transient failure on attempt %d/%d: %s",
                    attempt + 1,
                    self._max_retries + 1,
                    exc,
                )
                if attempt < self._max_retries:
                    await asyncio.sleep(_retry_delay(attempt, self._retry_backoff_seconds))

        raise LLMError(
            f"Gemini request failed after {self._max_retries + 1} attempt(s)"
        ) from last_error

    async def _call_model(
        self,
        *,
        system_prompt: str,
        messages: Sequence[ChatMessage],
        settings: GenerationSettings,
    ) -> LLMResult:
        try:
            from google import genai
            from google.genai import errors, types
        except ImportError as exc:
            raise LLMNotConfiguredError(
                "The Gemini SDK is not installed; install the 'llm' extra"
            ) from exc

        client = genai.Client(
            api_key=self._api_key,
            http_options=types.HttpOptions(timeout=int(self._timeout_seconds * 1000)),
        )
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=settings.temperature,
            max_output_tokens=settings.max_output_tokens,
            response_mime_type="application/json" if settings.json_output else None,
        )
        contents = [
            types.Content(role=_GEMINI_ROLES[message.role], parts=[types.Part(text=message.content)])
            for message in messages
        ]

        try:
            response = await client.aio.models.generate_content(
                model=self._model,
                contents=contents,
                config=config,
            )
        except errors.APIError as exc:
            if exc.code == 429 or exc.code >= 500:
                raise LLMTransientError(f"Gemini API returned {exc.code}") from exc
            raise LLMError(f"Gemini API rejected the request ({exc.code})") from exc
        except httpx.HTTPError as exc:
            raise LLMTransientError("Gemini transport error") from exc

        text = response.text
        if text is None or not text.strip():
            raise LLMError("Gemini returned an empty response")

        usage = response.usage_metadata
        return LLMResult(
            text=text,
            prompt_tokens=usage.prompt_token_count if usage is not None else None,
            completion_tokens=usage.candidates_token_count if usage is not None else None,
        )


    async def stream(
        self,
        *,
        system_prompt: str,
        messages: Sequence[ChatMessage],
        settings: GenerationSettings | None = None,
    ) -> AsyncIterator[LLMStreamEvent]:
        if not self._api_key:
            raise LLMNotConfiguredError("GEMINI_API_KEY is not set")

        resolved = settings or GenerationSettings()
        try:
            from google import genai
            from google.genai import errors, types
        except ImportError as exc:
            raise LLMNotConfiguredError(
                "The Gemini SDK is not installed; install the 'llm' extra"
            ) from exc

        client = genai.Client(
            api_key=self._api_key,
            http_options=types.HttpOptions(timeout=int(self._timeout_seconds * 1000)),
        )
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=resolved.temperature,
            max_output_tokens=resolved.max_output_tokens,
            response_mime_type="application/json" if resolved.json_output else None,
        )
        contents = [
            types.Content(role=_GEMINI_ROLES[message.role], parts=[types.Part(text=message.content)])
            for message in messages
        ]

        try:
            stream = await client.aio.models.generate_content_stream(
                model=self._model,
                contents=contents,
                config=config,
            )
            async for chunk in stream:
                usage = chunk.usage_metadata
                yield LLMStreamEvent(
                    text=chunk.text or "",
                    prompt_tokens=usage.prompt_token_count if usage is not None else None,
                    completion_tokens=(
                        usage.candidates_token_count if usage is not None else None
                    ),
                )
        except errors.APIError as exc:
            if exc.code == 429 or exc.code >= 500:
                raise LLMTransientError(f"Gemini API returned {exc.code}") from exc
            raise LLMError(f"Gemini API rejected the request ({exc.code})") from exc
        except httpx.HTTPError as exc:
            raise LLMTransientError("Gemini transport error") from exc


def get_llm_client() -> LLMClient:
    return GeminiLLMClient()


LLMClientDep = Annotated[LLMClient, Depends(get_llm_client)]
