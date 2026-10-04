from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class MorphologyAnalyzeRequest(BaseModel):
    word: str = Field(
        ..., min_length=1, max_length=100, description="Arabic word token to analyze"
    )


class ConjugateRequest(BaseModel):
    root: str = Field(..., min_length=3, max_length=10, description="Tri-literal Arabic root")
    form: int = Field(..., ge=1, le=10, description="Verb form 1..10")


class ConjugateResponse(BaseModel):
    root: str
    form: int
    supported: bool
    unsupported_reason: str | None = None
    past: str | None = None
    present: str | None = None
    imperative: str | None = None
    verbal_noun_pattern: str | None = None
    form_name: str | None = None


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
    source: str = Field(default="rules", description="corpus | camel | rules")
    pattern: str | None = None
    features_json: dict[str, Any] | None = None


class PatternExample(BaseModel):
    surah_number: int
    ayah_number: int
    word_position: int
    word_text: str
    lemma: str | None = None


class NounPatternItem(BaseModel):
    pattern: str
    name: str
    example: PatternExample | None = None


class PatternsResponse(BaseModel):
    verb_forms: list[VerbFormInfo]
    noun_patterns: list[NounPatternItem]


class WordFamilyGroup(BaseModel):
    pos_tag: str | None = None
    lemma: str | None = None
    count: int
    example: PatternExample | None = None


class WordFamilyResponse(BaseModel):
    root: str
    total_occurrences: int
    groups: list[WordFamilyGroup]


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
