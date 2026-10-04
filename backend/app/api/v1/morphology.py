from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.schemas.morphology import (
    ConjugateRequest,
    ConjugateResponse,
    MorphologyAnalyzeRequest,
    MorphologyAnalyzeResponse,
    PatternsResponse,
    RootConcordanceResponse,
    SegmentationDetail,
    VerbFormInfo,
    WordFamilyResponse,
)
from app.services.morphology_service import MorphologyService

router = APIRouter(prefix="/morphology", tags=["Morphology (Sarf)"])


@router.post("/analyze", response_model=MorphologyAnalyzeResponse)
async def analyze_word(
    req: MorphologyAnalyzeRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Analyze an Arabic word: clitic segmentation, tri-literal root extraction,

    Quranic lemma lookup, and verb form identification.
    """
    service = MorphologyService(db)
    return await service.analyze_word(req.word)


@router.post("/conjugate", response_model=ConjugateResponse)
async def conjugate(
    req: ConjugateRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Past/present/imperative paradigm for a sound tri-literal root.

    Weak, hamzated and doubled roots return supported=false with an
    unsupported_reason rather than possibly-wrong forms.
    """
    service = MorphologyService(db)
    return service.conjugate_word(req.root, req.form)


@router.get("/segment", response_model=SegmentationDetail)
def segment_word(
    word: str = Query(..., min_length=1, description="Word token to segment"),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Fast rule-based clitic segmentation (proclitics, stem, and enclitics)."""
    service = MorphologyService(db)
    return service.segment_clitics(word)


@router.get("/forms", response_model=list[VerbFormInfo])
def list_verb_forms(
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Reference list of all 10 Classical Arabic Derived Verb Forms (Awzan)."""
    service = MorphologyService(db)
    return service.list_verb_forms()


@router.get("/word-family/{root}", response_model=WordFamilyResponse)
async def get_word_family(
    root: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Group a root's distinct lemmas by pos_tag with counts and one example verse each."""
    service = MorphologyService(db)
    return await service.get_word_family(root)


@router.get("/patterns", response_model=PatternsResponse)
async def list_patterns(
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Verb forms catalog plus common noun patterns, with examples from the DB."""
    service = MorphologyService(db)
    return await service.list_patterns()


@router.get("/roots/{root}", response_model=RootConcordanceResponse)
async def get_root_concordance(
    root: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Quranic root concordance: total occurrences, derived lemmas, and sample verse citations."""
    service = MorphologyService(db)
    return await service.get_root_concordance(root)
