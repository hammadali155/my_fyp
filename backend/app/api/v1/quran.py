from __future__ import annotations

from fastapi import APIRouter, Query

from app.core.deps import DbSession
from app.core.logging import get_logger
from app.schemas.quran import (
    QuranSearchResponse,
    SurahListResponse,
    SurahResponse,
    VerseListResponse,
    VerseResponse,
)
from app.services.quran_service import QuranService

router = APIRouter(prefix="/quran", tags=["Quran Corpus"])
logger = get_logger("api.quran")


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
    "/verses",
    response_model=VerseListResponse,
    summary="List Quranic verses with pagination, optional surah or juz filtering",
)
async def list_verses(
    db: DbSession,
    surah_id: int | None = Query(default=None, description="Filter by Surah ID (1-114)"),
    juz_number: int | None = Query(default=None, description="Filter by Juz number (1-30)"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Page size"),
) -> VerseListResponse:
    service = QuranService(db)
    verses, total = await service.list_verses(
        surah_id=surah_id,
        juz_number=juz_number,
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
    summary="Search the Quran text (Arabic Uthmani / Imlaei) and translations",
)
async def search_quran(
    db: DbSession,
    q: str = Query(..., min_length=2, description="Search query string"),
    limit: int = Query(default=30, ge=1, le=100, description="Maximum matches to return"),
) -> QuranSearchResponse:
    service = QuranService(db)
    items, total = await service.search(query=q, limit=limit)
    return QuranSearchResponse(query=q, total=total, items=items)
