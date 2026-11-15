from __future__ import annotations

from typing import NoReturn

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.elements import ColumnElement

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.quran import NahwAnnotation, Surah, Verse
from app.schemas.nahw import NahwToken
from app.services.nahw_mapping import dep_label_to_role

logger = get_logger("services.nahw")

_MAX_AMBIGUOUS_CANDIDATES = 20

ROLE_DEFINITIONS: list[tuple[str, str, str]] = [
    ("جواب الشرط", "condition_answer", "Answer to a condition"),
    ("نائب فاعل", "naib_fail", "Deputy subject"),
    ("مفعول مطلق", "absolute_object", "Absolute object"),
    ("مفعول به", "object", "Object"),
    ("مضاف إليه", "mudaf_ilayhi", "Mudaf ilayhi (possessor)"),
    ("حرف جر", "preposition", "Preposition"),
    ("مبتدأ", "mubtada", "Mubtada"),
    ("مجرور", "genitive", "Genitive"),
    ("متعلق", "attachment", "Attachment (muta'allaq)"),
    ("معطوف", "conjoined", "Conjoined"),
    ("توكيد", "emphasis", "Emphasis"),
    ("تمييز", "specifier", "Specifier"),
    ("منادى", "vocative", "Vocative"),
    ("استفهام", "interrogative", "Interrogative"),
    ("تحقيق", "affirmation", "Affirmation"),
    ("فاعل", "subject", "Subject"),
    ("خبر", "khabar", "Khabar"),
    ("نعت", "adjective", "Adjective"),
    ("صفة", "adjective", "Adjective"),
    ("بدل", "appositive", "Appositive"),
    ("صلة", "relative_clause", "Relative clause"),
    ("حال", "circumstantial", "Circumstantial"),
    ("ظرف", "adverb", "Adverb"),
    ("شرط", "condition", "Condition"),
    ("حصر", "restriction", "Restriction"),
    ("نهي", "prohibition", "Prohibition"),
    ("نفي", "negation", "Negation"),
    ("تسوية", "equalization", "Equalization"),
    ("مركب", "compound", "Compound"),
    ("root", "root", "Sentence root"),
]

ROLE_EXACT: dict[str, tuple[str, str]] = {
    "NonRel": ("non_relation", "No relation"),
    "أمر": ("imperative", "Imperative"),
    "جواب": ("answer", "Answer"),
    "جواب أمر": ("imperative_answer", "Answer to an imperative"),
}

_ISMINNA_PARTICLES = frozenset({"إن", "أن", "كأن", "لكن", "لاكن", "ليت", "لعل"})
_ISMKANA_VERBS = frozenset(
    {
        "كان",
        "كانت",
        "يكون",
        "تكون",
        "يكن",
        "تكن",
        "ليس",
        "أصبح",
        "يصبح",
        "أمسى",
        "ظل",
        "يزال",
        "دام",
        "بات",
        "صار",
    }
)
_ISMKADA_VERBS = frozenset({"كاد", "يكاد", "تكاد", "عسى", "أوشك"})
_ISM_PREFIX = "اسم "

_ROLE_MARKERS = sorted(ROLE_DEFINITIONS, key=lambda item: len(item[0]), reverse=True)


def role_info(role_ar: str | None) -> tuple[str, str]:
    """Map an Arabic Nahw role to (role_key, English gloss) from the UI legend.

    Exact labels win first, then the longest matching Arabic marker, so a
    compound label (``نائب فاعل``) is never swallowed by a shorter marker
    (``فاعل``). Unmapped labels fall back to ``other`` — the raw label is
    always still returned to the client as ``role_ar``.
    """
    if not role_ar:
        return "other", "Other"
    normalized = role_ar.strip()
    exact = ROLE_EXACT.get(normalized)
    if exact is not None:
        return exact
    if normalized.startswith(_ISM_PREFIX):
        particle = normalized.removeprefix(_ISM_PREFIX).strip()
        if particle in _ISMINNA_PARTICLES:
            return "ism_inna", "Ism of إنّ or its sisters"
        if particle in _ISMKANA_VERBS:
            return "ism_kana", "Ism of كان or its sisters"
        if particle in _ISMKADA_VERBS:
            return "ism_kada", "Ism of كاد or its sisters"
        return "ism_particle", "Ism of a preceding particle"
    for marker, key, gloss in _ROLE_MARKERS:
        if marker in normalized:
            return key, gloss
    return "other", "Other"


class NahwService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_verse_annotations(self, surah_number: int, ayah_number: int) -> list[NahwToken]:
        logger.debug("Fetching Nahw annotations for %d:%d", surah_number, ayah_number)
        verse = (
            await self.db.execute(
                select(Verse)
                .join(Surah, Verse.surah_id == Surah.id)
                .where(Surah.number == surah_number, Verse.ayah_number == ayah_number)
            )
        ).scalar_one_or_none()
        if verse is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Verse {surah_number}:{ayah_number} not found",
            )

        result = await self.db.execute(
            select(NahwAnnotation)
            .options(selectinload(NahwAnnotation.word))
            .where(NahwAnnotation.verse_id == verse.id)
            .order_by(NahwAnnotation.token_index.asc())
        )
        annotations = list(result.scalars().all())
        if not annotations:
            return []

        tokens: list[NahwToken] = []
        for ann in annotations:
            key, gloss = role_info(ann.role)
            tokens.append(
                NahwToken(
                    position=ann.token_index,
                    text_uthmani=ann.word.text_uthmani if ann.word else "",
                    role_ar=ann.role,
                    role_en=gloss,
                    role_key=key,
                    dep_type=ann.dep_type,
                    irab=ann.irab,
                    head_index=ann.head_index,
                    head_surah_number=ann.head_surah_number,
                    head_ayah_number=ann.head_ayah_number,
                    sentence_index=ann.sentence_index,
                )
            )
        return tokens

    async def parse_text(self, text: str, is_quranic: bool = False) -> tuple[str, list[NahwToken]]:
        """Parse free text: corpus match first, else the Farasa sidecar.

        Returns (source, tokens) where source is "corpus" or "farasa".
        Raises 404 when the caller claims the text is Quranic but the corpus does
        not contain it, 409 when several verses share the text, 502 when the
        sidecar answers with a payload that cannot be used, and 503 when the
        sidecar is unreachable.
        """
        verse = await self._find_corpus_verse(text)
        if verse is not None:
            return "corpus", await self._tokens_for_verse(verse)

        if is_quranic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Text declared Quranic was not found in the corpus; refusing to parse it",
            )

        import httpx

        settings = get_settings()
        try:
            async with httpx.AsyncClient(timeout=settings.farasa_timeout_seconds) as client:
                resp = await client.post(f"{settings.farasa_url}/parse", json={"text": text})
                resp.raise_for_status()
                payload = resp.json()
        except httpx.HTTPStatusError as exc:
            logger.warning("Farasa sidecar returned %s", exc.response.status_code)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Nahw parsing service returned an error ({exc.response.status_code})",
            ) from exc
        except httpx.HTTPError as exc:
            logger.warning("Farasa sidecar unreachable: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Nahw parsing service (Farasa sidecar) is unreachable; try again later",
            ) from exc

        return "farasa", self._farasa_tokens(payload)

    def _farasa_tokens(self, payload: object) -> list[NahwToken]:
        if not isinstance(payload, dict):
            self._raise_malformed_farasa()
        raw_tokens = payload.get("tokens")
        if not isinstance(raw_tokens, list) or not raw_tokens:
            self._raise_malformed_farasa()

        tokens: list[NahwToken] = []
        for position, token in enumerate(raw_tokens, start=1):
            if not isinstance(token, dict):
                self._raise_malformed_farasa()
            surface = token.get("surface_form") or token.get("form") or token.get("text")
            if not isinstance(surface, str) or not surface.strip():
                self._raise_malformed_farasa()
            dep = token.get("dep_label") or token.get("dep") or ""
            role = dep_label_to_role(dep if isinstance(dep, str) else "")
            head = token.get("head")
            tokens.append(
                NahwToken(
                    position=position,
                    text_uthmani=surface,
                    role_ar=role.role_ar,
                    role_en=role.role_en,
                    role_key=role.role_key,
                    irab=None,
                    head_index=head if isinstance(head, int) else None,
                )
            )
        return tokens

    def _raise_malformed_farasa(self) -> NoReturn:
        logger.warning("Farasa sidecar returned a malformed payload")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Nahw parsing service returned a malformed response",
        )

    async def _corpus_rows(self, condition: ColumnElement[bool] | None = None) -> list[tuple[Verse, int]]:
        stmt = (
            select(Verse, Surah.number)
            .join(Surah, Verse.surah_id == Surah.id)
            .order_by(Verse.id)
        )
        if condition is not None:
            stmt = stmt.where(condition)
        rows = (await self.db.execute(stmt)).all()
        return [(row[0], row[1]) for row in rows]

    async def _find_corpus_verse(self, text: str) -> Verse | None:
        from app.services.morphology_service import normalize_arabic

        for condition in (Verse.text_uthmani == text, Verse.text_imlaei == text):
            rows = await self._corpus_rows(condition)
            if rows:
                return self._single_corpus_match(rows)

        norm = normalize_arabic(text)
        normalized = [
            (verse, surah_number)
            for verse, surah_number in await self._corpus_rows()
            if verse.text_imlaei and normalize_arabic(verse.text_imlaei) == norm
        ]
        if normalized:
            return self._single_corpus_match(normalized)
        return None

    def _single_corpus_match(self, rows: list[tuple[Verse, int]]) -> Verse:
        if len(rows) == 1:
            return rows[0][0]

        candidates = ", ".join(
            f"{surah_number}:{verse.ayah_number}"
            for verse, surah_number in rows[:_MAX_AMBIGUOUS_CANDIDATES]
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Text matches {len(rows)} verses ({candidates}); "
                "request one of them with /nahw/verse/{surah}/{ayah}"
            ),
        )

    async def _tokens_for_verse(self, verse: Verse) -> list[NahwToken]:
        result = await self.db.execute(
            select(NahwAnnotation)
            .options(selectinload(NahwAnnotation.word))
            .where(NahwAnnotation.verse_id == verse.id)
            .order_by(NahwAnnotation.token_index.asc())
        )
        tokens: list[NahwToken] = []
        for ann in result.scalars().all():
            key, gloss = role_info(ann.role)
            tokens.append(
                NahwToken(
                    position=ann.token_index,
                    text_uthmani=ann.word.text_uthmani if ann.word else "",
                    role_ar=ann.role,
                    role_en=gloss,
                    role_key=key,
                    dep_type=ann.dep_type,
                    irab=ann.irab,
                    head_index=ann.head_index,
                    head_surah_number=ann.head_surah_number,
                    head_ayah_number=ann.head_ayah_number,
                    sentence_index=ann.sentence_index,
                )
            )
        return tokens
