from __future__ import annotations

import asyncio
from typing import Annotated, Any, Protocol

import httpx
from fastapi import Depends

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("services.gemini")

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiError(RuntimeError):
    pass


class GeminiNotConfiguredError(GeminiError):
    pass


class GeminiClientProtocol(Protocol):
    async def generate(self, prompt: str) -> str: ...


class GeminiClient:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        timeout_seconds: float | None = None,
        max_retries: int | None = None,
        retry_backoff_seconds: float | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
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
        self._transport = transport

    async def generate(self, prompt: str) -> str:
        if not self._api_key:
            raise GeminiNotConfiguredError("GEMINI_API_KEY is not set")

        url = f"{GEMINI_BASE_URL}/{self._model}:generateContent"
        headers = {"x-goog-api-key": self._api_key}
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        last_error: Exception | None = None

        for attempt in range(self._max_retries + 1):
            try:
                async with httpx.AsyncClient(
                    timeout=self._timeout_seconds, transport=self._transport
                ) as client:
                    response = await client.post(url, json=payload, headers=headers)
            except httpx.TransportError as exc:
                last_error = exc
                logger.warning("Gemini transport error on attempt %d: %s", attempt + 1, exc)
                if attempt < self._max_retries:
                    await asyncio.sleep(self._retry_backoff_seconds * (attempt + 1))
                continue

            status_code = response.status_code
            if status_code == 429 or status_code >= 500:
                last_error = GeminiError(f"Gemini API returned {status_code}")
                logger.warning("Gemini returned %d on attempt %d", status_code, attempt + 1)
                if attempt < self._max_retries:
                    await asyncio.sleep(self._retry_backoff_seconds * (attempt + 1))
                continue

            if status_code >= 400:
                raise GeminiError(f"Gemini API rejected the request ({status_code})")

            try:
                return self._extract_text(response.json())
            except (ValueError, GeminiError) as exc:
                raise GeminiError("Gemini returned an unusable response") from exc

        raise GeminiError("Gemini request failed after retries") from last_error

    def _extract_text(self, payload: Any) -> str:
        if not isinstance(payload, dict):
            raise GeminiError("Gemini response was not an object")
        candidates = payload.get("candidates")
        if not isinstance(candidates, list) or not candidates:
            raise GeminiError("Gemini response had no candidates")
        first = candidates[0]
        if not isinstance(first, dict):
            raise GeminiError("Gemini candidate was not an object")
        content = first.get("content")
        if not isinstance(content, dict):
            raise GeminiError("Gemini candidate had no content")
        parts = content.get("parts")
        if not isinstance(parts, list):
            raise GeminiError("Gemini content had no parts")
        chunks: list[str] = []
        for part in parts:
            if isinstance(part, dict):
                text = part.get("text")
                if isinstance(text, str):
                    chunks.append(text)
        if not chunks:
            raise GeminiError("Gemini response had no text")
        return "".join(chunks)


def get_gemini_client() -> GeminiClient:
    return GeminiClient()


GeminiClientDep = Annotated[GeminiClientProtocol, Depends(get_gemini_client)]
