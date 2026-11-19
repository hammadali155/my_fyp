from __future__ import annotations

from fastapi import APIRouter

from app.core.deps import CurrentUser, DbSession
from app.core.logging import get_logger
from app.schemas.nahw import (
    NahwExplainResponse,
    NahwParseRequest,
    NahwParseResponse,
    NahwVerseResponse,
)
from app.services.llm_client import LLMClientDep
from app.services.nahw_explain_service import NahwExplainService, normalize_language
from app.services.nahw_service import NahwService

router = APIRouter(prefix="/nahw", tags=["Nahw (Syntax)"])
logger = get_logger("api.nahw")


@router.post(
    "/parse",
    response_model=NahwParseResponse,
    summary="Parse free text with the corpus treebank or the Farasa sidecar",
)
async def parse_text(
    req: NahwParseRequest, db: DbSession
) -> NahwParseResponse:
    """Parse free text: exact corpus match returns gold annotations (source=corpus);
    otherwise the Farasa sidecar is called (source=farasa). 503 if unreachable."""
    service = NahwService(db)
    source, tokens = await service.parse_text(req.text, req.is_quranic)
    return NahwParseResponse(source=source, tokens=tokens)


@router.get(
    "/verse/{surah_number}/{ayah_number}",
    response_model=NahwVerseResponse,
    summary="Get Nahw (syntax) annotations for a verse",
)
async def get_verse_annotations(
    surah_number: int, ayah_number: int, db: DbSession
) -> NahwVerseResponse:
    service = NahwService(db)
    tokens = await service.get_verse_annotations(surah_number, ayah_number)
    if not tokens:
        return NahwVerseResponse(
            surah_number=surah_number,
            ayah_number=ayah_number,
            tokens=[],
            has_annotations=False,
            message="No treebank data available for this verse (empty response, no guess made).",
        )
    return NahwVerseResponse(
        surah_number=surah_number,
        ayah_number=ayah_number,
        tokens=tokens,
        has_annotations=True,
    )


@router.get(
    "/explain/{word_id}",
    response_model=NahwExplainResponse,
    summary="Explain one word's i'rab grounded in stored word, verse and treebank data",
)
async def explain_word(
    word_id: int,
    db: DbSession,
    current_user: CurrentUser,
    llm: LLMClientDep,
) -> NahwExplainResponse:
    service = NahwExplainService(db, llm)
    language = normalize_language(current_user.ui_lang)
    return await service.explain(word_id, language)
