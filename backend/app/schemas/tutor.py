from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, model_validator

MAX_TUTOR_MESSAGE_CHARS = 2000


class TutorReference(BaseModel):
    surah_number: int | None = Field(default=None, ge=1, le=114)
    ayah_number: int | None = Field(default=None, ge=1)
    word_id: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def _check_reference(self) -> TutorReference:
        if self.word_id is not None and self.surah_number is not None:
            raise ValueError("Provide either word_id or surah_number, not both")
        if self.word_id is None and self.surah_number is None:
            raise ValueError("Provide word_id or surah_number")
        if self.ayah_number is not None and self.surah_number is None:
            raise ValueError("ayah_number requires surah_number")
        return self


class TutorChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=MAX_TUTOR_MESSAGE_CHARS)
    session_id: int | None = Field(default=None, ge=1)
    reference: TutorReference | None = None


class TutorCitationOut(BaseModel):
    surah: int
    ayah: int


class TutorUsage(BaseModel):
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


class TutorChatResponse(BaseModel):
    session_id: int
    reply: str
    citations: list[TutorCitationOut]
    model: str
    usage: TutorUsage
    truncated_context: bool = False
    unresolved_references: list[str] = Field(default_factory=list)
    incomplete: bool = False


class TutorSessionSummary(BaseModel):
    id: int
    title: str
    message_count: int
    created_at: datetime
    updated_at: datetime


class TutorSessionList(BaseModel):
    sessions: list[TutorSessionSummary]
