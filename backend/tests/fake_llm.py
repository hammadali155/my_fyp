from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass

from app.services.llm_client import (
    ChatMessage,
    GenerationSettings,
    LLMClient,
    LLMResult,
    LLMStreamEvent,
)


@dataclass
class LLMCall:
    system_prompt: str
    messages: list[ChatMessage]
    settings: GenerationSettings


class FakeLLMClient(LLMClient):
    """Scripted LLM used by tests. Never touches the network."""

    def __init__(
        self,
        *,
        reply: str = "fake reply",
        error: Exception | None = None,
        prompt_tokens: int | None = 12,
        completion_tokens: int | None = 6,
        stream_chunks: list[str] | None = None,
        stream_error: Exception | None = None,
        stream_error_after: int | None = None,
    ) -> None:
        self.reply = reply
        self.error = error
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.stream_chunks = stream_chunks
        self.stream_error = stream_error
        self.stream_error_after = stream_error_after
        self.calls: list[LLMCall] = []
        self.stream_calls: list[LLMCall] = []

    @property
    def prompts(self) -> list[str]:
        return [
            call.system_prompt + "\n" + "\n".join(message.content for message in call.messages)
            for call in self.calls
        ]

    async def generate(
        self,
        *,
        system_prompt: str,
        messages: Sequence[ChatMessage],
        settings: GenerationSettings | None = None,
    ) -> LLMResult:
        resolved = settings or GenerationSettings()
        self.calls.append(
            LLMCall(
                system_prompt=system_prompt,
                messages=list(messages),
                settings=resolved,
            )
        )
        if self.error is not None:
            raise self.error
        return LLMResult(
            text=self.reply,
            prompt_tokens=self.prompt_tokens,
            completion_tokens=self.completion_tokens,
        )

    async def stream(
        self,
        *,
        system_prompt: str,
        messages: Sequence[ChatMessage],
        settings: GenerationSettings | None = None,
    ) -> AsyncIterator[LLMStreamEvent]:
        resolved = settings or GenerationSettings()
        self.stream_calls.append(
            LLMCall(
                system_prompt=system_prompt,
                messages=list(messages),
                settings=resolved,
            )
        )
        chunks = self.stream_chunks if self.stream_chunks is not None else [self.reply]
        error_after = self.stream_error_after
        if self.stream_error is not None and (error_after is None or error_after <= 0):
            raise self.stream_error
        for index, text in enumerate(chunks):
            if self.stream_error is not None and error_after is not None and index >= error_after:
                raise self.stream_error
            last = index == len(chunks) - 1
            yield LLMStreamEvent(
                text=text,
                prompt_tokens=self.prompt_tokens if last else None,
                completion_tokens=self.completion_tokens if last else None,
            )
        if self.stream_error is not None and (
            error_after is None or error_after >= len(chunks)
        ):
            raise self.stream_error
