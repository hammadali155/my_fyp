from __future__ import annotations

from pydantic import BaseModel, Field


class MorphologyAnalyzeRequest(BaseModel):
    word: str = Field(..., min_length=1, max_length=100, description="Arabic word token to analyze")


class CliticDetail(BaseModel):
    clitic: str
    meaning: str
    type: str


class SegmentationDetail(BaseModel):
    original: str
    normalized: str
    prefix: CliticDetail | None = None
    stem: str
    suffix: CliticDetail | None = None


class VerbFormInfo(BaseModel):
    form_number: int
    name: str
    pattern_past: str
    pattern_present: str
    verbal_noun: str
    description: str


class MorphologyAnalyzeResponse(BaseModel):
    word: str
    normalized: str
    segmentation: SegmentationDetail
    root: str | None = None
    lemma: str | None = None
    pos_tag: str | None = None
    detected_form: VerbFormInfo | None = None
    is_quranic: bool


class LemmaCount(BaseModel):
    lemma: str
    count: int


class RootCitation(BaseModel):
    surah_number: int
    surah_name: str
    surah_name_arabic: str
    ayah_number: int
    word_position: int
    word_text: str
    verse_text: str
    verse_translation_en: str | None = None


class RootConcordanceResponse(BaseModel):
    root: str
    total_occurrences: int
    distinct_lemmas: list[LemmaCount]
    citations: list[RootCitation]
