from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.quran import NahwAnnotation, Surah, Verse, Word
from app.services.morphology_service import normalize_arabic

logger = get_logger("services.tutor_context")

NOT_AVAILABLE = "not available in corpus"
MAX_REFERENCES = 3

VERSE_REFERENCE_RE = re.compile(r"\b([1-9]\d{0,2})\s*[:：]\s*([1-9]\d{0,2})\b")
SURAH_NAME_RE = re.compile(r"(?:surah|surat)\s+([A-Za-z][A-Za-z'\-]{1,30})", re.IGNORECASE)
ARABIC_SURAH_NAME_RE = re.compile(r"سورة\s+([\u0600-\u06ff]+)")

TRANSLATION_ATTRS: dict[str, str] = {"en": "translation_en", "ur": "translation_ur"}

INTRO = (
    "[Quran context — read-only corpus data. "
    "Do not alter Quranic text, translations or annotations.]"
)


@dataclass(frozen=True)
class ContextReference:
    surah_number: int | None = None
    ayah_number: int | None = None
    word_id: int | None = None


@dataclass(frozen=True)
class TutorCitation:
    surah: int
    ayah: int

    def as_dict(self) -> dict[str, int]:
        return {"surah": self.surah, "ayah": self.ayah}


@dataclass
class TutorContext:
    text: str
    citations: list[TutorCitation] = field(default_factory=list)
    unresolved_references: list[str] = field(default_factory=list)
    truncated: bool = False
    verse_ids: list[int] = field(default_factory=list)


def _name_key(name: str) -> str:
    cleaned = normalize_arabic(name).lower()
    return re.sub(r"[\s\-'’`.]", "", cleaned)


def extract_message_references(message: str) -> list[tuple[str, int | None, int | None]]:
    """Returns (label, surah_number, ayah_number); surah_number is None for a name."""
    found: list[tuple[str, int | None, int | None]] = []
    for match in VERSE_REFERENCE_RE.finditer(message):
        label = match.group(0).strip()
        found.append((label, int(match.group(1)), int(match.group(2))))
    for pattern in (SURAH_NAME_RE, ARABIC_SURAH_NAME_RE):
        for match in pattern.finditer(message):
            label = match.group(1).strip()
            if any(label == existing[0] for existing in found):
                continue
            found.append((label, None, None))
    return found[:MAX_REFERENCES]


def apply_char_cap(sections: list[str], max_chars: int) -> tuple[str, bool]:
    """Joins sections in priority order; the first section that overflows is cut."""
    kept: list[str] = []
    used = 0
    for section in sections:
        separator = "\n\n" if kept else ""
        remaining = max_chars - used - len(separator)
        if len(section) <= remaining:
            kept.append(section)
            used += len(separator) + len(section)
            continue
        if remaining > 0:
            partial = section[:remaining]
            line_break = partial.rfind("\n")
            if line_break >= len(partial) // 2:
                partial = partial[:line_break]
            if partial:
                kept.append(partial)
        return "\n\n".join(kept).rstrip(), True
    return "\n\n".join(kept).rstrip(), False


class TutorContextService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def build(
        self,
        *,
        message: str,
        languages: Sequence[str] = ("en",),
        reference: ContextReference | None = None,
        max_chars: int | None = None,
    ) -> TutorContext:
        limit = max_chars if max_chars is not None else get_settings().tutor_context_max_chars
        verses, unresolved = await self._resolve_targets(message=message, reference=reference)
        highlighted_word_id = reference.word_id if reference is not None else None

        logger.debug(
            "Built tutor context targets=%d unresolved=%d max_chars=%d",
            len(verses),
            len(unresolved),
            limit,
        )

        sections: list[str] = []
        if not verses and not unresolved:
            sections.append(
                "[Quran context]\n"
                "No Quranic reference was found in the message. No verse data is included; "
                "do not cite a verse unless the learner names one."
            )
        else:
            annotations = await self._load_nahw([verse.id for verse in verses])
            for verse in verses:
                sections.append(
                    self._render_verse(
                        verse,
                        languages,
                        annotations.get(verse.id, []),
                        highlighted_word_id,
                        intro=not sections,
                    )
                )
            if unresolved:
                sections.append(self._render_unresolved(unresolved))

        text, truncated = apply_char_cap(sections, limit)
        return TutorContext(
            text=text,
            citations=[
                TutorCitation(surah=verse.surah.number, ayah=verse.ayah_number)
                for verse in verses
            ],
            unresolved_references=unresolved,
            truncated=truncated,
            verse_ids=[verse.id for verse in verses],
        )

    async def _resolve_targets(
        self, *, message: str, reference: ContextReference | None
    ) -> tuple[list[Verse], list[str]]:
        verses: list[Verse] = []
        unresolved: list[str] = []
        seen: set[int] = set()

        def add(verse: Verse) -> None:
            if verse.id not in seen:
                seen.add(verse.id)
                verses.append(verse)

        if reference is not None:
            verse, label = await self._resolve_explicit(reference)
            if verse is None:
                unresolved.append(label)
            else:
                add(verse)

        for label, surah_number, ayah_number in extract_message_references(message):
            if surah_number is None:
                surah = await self._match_surah_name(label)
                verse = (
                    None
                    if surah is None
                    else await self._load_verse(surah.number, ayah_number)
                )
                if verse is None and surah is not None:
                    label = f"{surah.number}:{ayah_number or 1}"
            else:
                verse = await self._load_verse(surah_number, ayah_number)
            if verse is None:
                if label not in unresolved:
                    unresolved.append(label)
            else:
                add(verse)

        return verses, unresolved

    async def _resolve_explicit(
        self, reference: ContextReference
    ) -> tuple[Verse | None, str]:
        if reference.word_id is not None:
            word = await self.db.get(Word, reference.word_id)
            if word is None:
                return None, f"word {reference.word_id}"
            verse = await self._load_verse_by_id(word.verse_id)
            if verse is None:
                return None, f"word {reference.word_id}"
            return verse, f"word {reference.word_id}"
        if reference.surah_number is None:
            return None, "reference"
        label = f"{reference.surah_number}:{reference.ayah_number or 1}"
        verse = await self._load_verse(reference.surah_number, reference.ayah_number)
        return verse, label

    async def _match_surah_name(self, name: str) -> Surah | None:
        key = _name_key(name)
        if not key:
            return None
        result = await self.db.execute(select(Surah).order_by(Surah.number.asc()))
        surahs = list(result.scalars().all())
        for surah in surahs:
            names = (
                surah.name_transliteration,
                surah.name_english,
                surah.name_arabic,
            )
            if any(_name_key(candidate) == key for candidate in names):
                return surah
        if len(key) >= 3:
            for surah in surahs:
                names = (
                    surah.name_transliteration,
                    surah.name_english,
                    surah.name_arabic,
                )
                if any(_name_key(candidate).endswith(key) for candidate in names):
                    return surah
        return None

    async def _load_verse(self, surah_number: int, ayah_number: int | None) -> Verse | None:
        stmt = (
            select(Verse)
            .join(Surah, Verse.surah_id == Surah.id)
            .options(joinedload(Verse.surah), selectinload(Verse.words))
            .where(
                Surah.number == surah_number,
                Verse.ayah_number == (ayah_number or 1),
            )
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def _load_verse_by_id(self, verse_id: int) -> Verse | None:
        stmt = (
            select(Verse)
            .options(joinedload(Verse.surah), selectinload(Verse.words))
            .where(Verse.id == verse_id)
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def _load_nahw(self, verse_ids: list[int]) -> dict[int, list[NahwAnnotation]]:
        if not verse_ids:
            return {}
        stmt = (
            select(NahwAnnotation)
            .where(NahwAnnotation.verse_id.in_(verse_ids))
            .order_by(NahwAnnotation.verse_id.asc(), NahwAnnotation.token_index.asc())
        )
        result = await self.db.execute(stmt)
        grouped: dict[int, list[NahwAnnotation]] = {}
        for annotation in result.scalars().all():
            grouped.setdefault(annotation.verse_id, []).append(annotation)
        return grouped

    def _render_verse(
        self,
        verse: Verse,
        languages: Sequence[str],
        annotations: list[NahwAnnotation],
        highlighted_word_id: int | None,
        *,
        intro: bool,
    ) -> str:
        surah = verse.surah
        lines: list[str] = []
        if intro:
            lines.append(INTRO)
        lines.append(
            f"Surah {surah.number} {surah.name_transliteration} "
            f"({surah.name_arabic}) — {surah.name_english}"
        )
        lines.append(f"Verse {surah.number}:{verse.ayah_number}")
        lines.append(f"Uthmani: {verse.text_uthmani}")
        lines.append(f"Imlaei: {verse.text_imlaei or NOT_AVAILABLE}")
        for language in languages:
            attr = TRANSLATION_ATTRS.get(language)
            if attr is None:
                lines.append(f"Translation ({language}): {NOT_AVAILABLE}")
                continue
            lines.append(f"Translation ({language}): {getattr(verse, attr) or NOT_AVAILABLE}")

        words = sorted(verse.words, key=lambda word: word.position)
        if words:
            lines.append("Words:")
            for word in words:
                parts = [
                    f"  {word.position}. {word.text_uthmani}",
                    f"root {word.root or 'n/a'}",
                    f"lemma {word.lemma or 'n/a'}",
                    f"pos {word.pos_tag or 'n/a'}",
                ]
                if word.translation_en:
                    parts.append(f"gloss {word.translation_en}")
                if word.id == highlighted_word_id:
                    parts.append("referenced word")
                lines.append(" | ".join(parts))
        else:
            lines.append(f"Words: {NOT_AVAILABLE}")

        if not annotations:
            lines.append(f"Nahw: {NOT_AVAILABLE}")
        else:
            lines.append("Nahw:")
            for annotation in annotations:
                details = [f"  {annotation.token_index}."]
                if annotation.word_id is not None:
                    position = next(
                        (word.position for word in words if word.id == annotation.word_id),
                        None,
                    )
                    if position is not None:
                        details.append(f"word={position}")
                if annotation.role:
                    details.append(f"role={annotation.role}")
                if annotation.dep_type:
                    details.append(f"dep={annotation.dep_type}")
                if annotation.head_index is not None:
                    details.append(f"head={annotation.head_index}")
                if annotation.irab:
                    details.append(f"irab={annotation.irab}")
                if annotation.sentence_index is not None:
                    details.append(f"sentence={annotation.sentence_index}")
                lines.append(" ".join(details))

        return "\n".join(lines)

    def _render_unresolved(self, unresolved: list[str]) -> str:
        lines = ["[Unresolved references]"]
        for label in unresolved:
            lines.append(
                f"Reference {label}: not found in the corpus. "
                "No verse data is included for it; do not guess its text or meaning."
            )
        return "\n".join(lines)
