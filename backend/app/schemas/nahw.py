from __future__ import annotations

from pydantic import BaseModel, Field

_HEAD_INDEX_DESCRIPTION = (
    "Head word position: >= 1 means the head's position in the verse named by "
    "head_surah_number/head_ayah_number; -1 means no separate head word "
    "(sentence root or a clitic attached to this same word); 0 means the head is "
    "an elided element the corpus records as a placeholder. Both sentinel values "
    "carry null head verse fields."
)


class NahwToken(BaseModel):
    position: int
    text_uthmani: str
    role_ar: str | None = None
    role_en: str
    role_key: str
    dep_type: str | None = None
    irab: str | None = None
    head_index: int | None = Field(default=None, description=_HEAD_INDEX_DESCRIPTION)
    head_surah_number: int | None = None
    head_ayah_number: int | None = None
    sentence_index: int | None = None


class NahwVerseResponse(BaseModel):
    surah_number: int
    ayah_number: int
    tokens: list[NahwToken]
    has_annotations: bool = False
    message: str | None = None


class NahwParseRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    is_quranic: bool = False


class NahwParseResponse(BaseModel):
    source: str
    tokens: list[NahwToken]
