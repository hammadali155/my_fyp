from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class WordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    position: int
    text_uthmani: str
    text_imlaei: str | None = None
    translation_en: str | None = None
    transliteration: str | None = None
    root: str | None = None
    lemma: str | None = None
    pos_tag: str | None = None
    pattern: str | None = None
    tense: str | None = None
    voice: str | None = None
    gender: str | None = None
    number: str | None = None
    person: str | None = None
    features_json: dict[str, Any] | None = None


class VerseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    surah_id: int
    ayah_number: int
    text_uthmani: str
    text_imlaei: str | None = None
    translation_en: str | None = None
    translation_ur: str | None = None
    juz_number: int | None = None
    hizb_number: int | None = None
    page_number: int | None = None
    words: list[WordResponse] = []


class SurahResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    number: int
    name_arabic: str
    name_transliteration: str
    name_english: str
    revelation_place: str | None = None
    verse_count: int


class SurahDetailResponse(SurahResponse):
    pass


class SurahListResponse(BaseModel):
    items: list[SurahResponse]
    total: int


class VerseListResponse(BaseModel):
    items: list[VerseResponse]
    total: int
    surah: SurahResponse | None = None


class SearchMatchItem(BaseModel):
    surah_number: int
    surah_name_english: str
    ayah_number: int
    text_uthmani: str
    translation_en: str | None = None
    translation_ur: str | None = None
    matched_field: str


class QuranSearchResponse(BaseModel):
    query: str
    total: int
    items: list[SearchMatchItem]


class RootRankItem(BaseModel):
    root: str
    occurrence_count: int


class RootRankResponse(BaseModel):
    items: list[RootRankItem]
    total: int
