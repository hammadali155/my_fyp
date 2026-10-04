from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.core.deps import DbSession
from app.core.logging import get_logger
from app.schemas.common import PaginatedParams
from app.schemas.quran import (
    QuranSearchResponse,
    RootRankItem,
    RootRankResponse,
    SurahListResponse,
    SurahResponse,
    VerseListResponse,
    VerseResponse,
)
from app.services.quran_service import QuranService

router = APIRouter(prefix="/quran", tags=["Quran Corpus"])
logger = get_logger("api.quran")


async def pagination(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
) -> PaginatedParams:
    return PaginatedParams(page=page, page_size=page_size)


@router.get(
    "/surahs",
    response_model=SurahListResponse,
    summary="List all 114 Surahs of the Holy Quran",
)
async def list_surahs(db: DbSession) -> SurahListResponse:
    service = QuranService(db)
    surahs = await service.list_surahs()
    items = [SurahResponse.model_validate(s) for s in surahs]
    return SurahListResponse(items=items, total=len(items))


@router.get(
    "/surahs/{surah_id}",
    response_model=SurahResponse,
    summary="Get details of a specific Surah by ID or number",
)
async def get_surah(surah_id: int, db: DbSession) -> SurahResponse:
    service = QuranService(db)
    surah = await service.get_surah(surah_id)
    return SurahResponse.model_validate(surah)


@router.get(
    "/roots",
    response_model=RootRankResponse,
    summary="List roots ranked by occurrence count, with optional filters",
)
async def list_roots(
    db: DbSession,
    min_count: int | None = Query(default=None, ge=1, description="Minimum occurrences"),
    pos_tag: str | None = Query(default=None, description="Filter words by POS tag"),
    surah_number: int | None = Query(default=None, ge=1, le=114, description="Filter words by surah"),
    limit: int = Query(default=50, ge=1, le=500, description="Maximum roots returned"),
) -> RootRankResponse:
    service = QuranService(db)
    rows = await service.list_roots(min_count=min_count, pos_tag=pos_tag, surah_number=surah_number, limit=limit)
    items = [RootRankItem(root=root, occurrence_count=count) for root, count in rows]
    return RootRankResponse(items=items, total=len(items))


@router.get(
    "/verses",
    response_model=VerseListResponse,
    summary="List Quranic verses with pagination, optional surah or juz filtering",
)
async def list_verses(
    db: DbSession,
    surah_id: int | None = Query(default=None, description="Filter by Surah ID (1-114)"),
    juz_number: int | None = Query(default=None, description="Filter by Juz number (1-30)"),
    page_number: int | None = Query(default=None, description="Filter by mushaf page number"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Page size"),
) -> VerseListResponse:
    service = QuranService(db)
    verses, total = await service.list_verses(
        surah_id=surah_id,
        juz_number=juz_number,
        page_number=page_number,
        page=page,
        page_size=page_size,
    )

    surah_obj = None
    if surah_id is not None:
        try:
            surah_data = await service.get_surah(surah_id)
            surah_obj = SurahResponse.model_validate(surah_data)
        except Exception:
            surah_obj = None

    items = [VerseResponse.model_validate(v) for v in verses]
    return VerseListResponse(items=items, total=total, surah=surah_obj)


@router.get(
    "/surahs/{surah_number}/verses/{ayah_number}",
    response_model=VerseResponse,
    summary="Get a verse by surah number and ayah number with words and morphology",
)
async def get_verse_by_surah_ayah(
    surah_number: int, ayah_number: int, db: DbSession
) -> VerseResponse:
    service = QuranService(db)
    verse = await service.get_verse_by_surah_ayah(surah_number, ayah_number)
    return VerseResponse.model_validate(verse)


@router.get(
    "/verses/{verse_id}",
    response_model=VerseResponse,
    summary="Get a single verse by ID with its word-by-word breakdown",
)
async def get_verse(verse_id: int, db: DbSession) -> VerseResponse:
    service = QuranService(db)
    verse = await service.get_verse(verse_id)
    return VerseResponse.model_validate(verse)


@router.get(
    "/search",
    response_model=QuranSearchResponse,
    summary="Search the Quran text (Arabic normalized / Imlaei) and translations",
)
async def search_quran(
    db: DbSession,
    params: PaginatedParams = Depends(pagination),
    q: str = Query(..., min_length=2, description="Search query string"),
) -> QuranSearchResponse:
    service = QuranService(db)
    items, total = await service.search(query=q, page=params.page, page_size=params.page_size)
    return QuranSearchResponse(query=q, total=total, items=items)
