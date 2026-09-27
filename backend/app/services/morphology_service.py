"""Classical Arabic Morphology (Sarf) Engine.

Provides Arabic text normalization, clitic segmentation, tri-literal root identification,
derivational pattern (Wazn) analysis for Classical Arabic verb forms (Forms I - X),
and Quranic corpus frequency aggregation.
"""

from __future__ import annotations

import re
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.quran import Surah, Verse, Word

logger = get_logger("services.morphology")

# Arabic Diacritics (Harakat / Tashkeel) Unicode block
TASHKEEL_REGEX = re.compile(r"[\u0617-\u061A\u064B-\u0652\u0670\u06D6-\u06ED]")

# Classical Arabic 10 Derived Verb Forms (Forms I to X)
VERB_FORMS_CATALOG: list[dict[str, Any]] = [
    {
        "form": 1,
        "name": "Form I (فَعَلَ / يَفْعَلُ)",
        "pattern_past": "فَعَلَ",
        "pattern_present": "يَفْعَلُ",
        "verbal_noun": "فَعْل / فُعُول",
        "description": "Base primary stem representing the fundamental verbal root meaning.",
        "regex_template": r"^{r1}{r2}{r3}$",
    },
    {
        "form": 2,
        "name": "Form II (فَعَّلَ / يُفَعِّلُ)",
        "pattern_past": "فَعَّلَ",
        "pattern_present": "يُفَعِّلُ",
        "verbal_noun": "تَفْعِيل",
        "description": "Causative, intensive, or declarative meaning (e.g. عَلَّمَ 'he taught').",
        "regex_template": r"^{r1}{r2}{r2}{r3}$",
    },
    {
        "form": 3,
        "name": "Form III (فَاعَلَ / يُفَاعِلُ)",
        "pattern_past": "فَاعَلَ",
        "pattern_present": "يُفَاعِلُ",
        "verbal_noun": "مُفَاعَلَة / فِعَال",
        "description": "Reciprocity, association, or striving towards an action (e.g. جَاهَدَ 'he strove').",
        "regex_template": r"^{r1}ا{r2}{r3}$",
    },
    {
        "form": 4,
        "name": "Form IV (أَفْعَلَ / يُفْعِلُ)",
        "pattern_past": "أَفْعَلَ",
        "pattern_present": "يُفْعِلُ",
        "verbal_noun": "إِفْعَال",
        "description": "Transitive or causative stem (e.g. أَنْزَلَ 'he sent down', أَسْلَمَ 'he submitted').",
        "regex_template": r"^أ{r1}{r2}{r3}$",
    },
    {
        "form": 5,
        "name": "Form V (تَفَعَّلَ / يَتَفَعَّلُ)",
        "pattern_past": "تَفَعَّلَ",
        "pattern_present": "يَتَفَعَّلُ",
        "verbal_noun": "تَفَعُّل",
        "description": "Reflexive of Form II; gradual or reflective action (e.g. تَذَكَّرَ 'he reflected/remembered').",
        "regex_template": r"^ت{r1}{r2}{r2}{r3}$",
    },
    {
        "form": 6,
        "name": "Form VI (تَفَاعَلَ / يَتَفَاعَلُ)",
        "pattern_past": "تَفَاعَلَ",
        "pattern_present": "يَتَفَاعَلُ",
        "verbal_noun": "تَفَاعُل",
        "description": "Mutual cooperation, reciprocity, or simulation (e.g. تَعَاوَنَ 'they cooperated').",
        "regex_template": r"^ت{r1}ا{r2}{r3}$",
    },
    {
        "form": 7,
        "name": "Form VII (انْفَعَلَ / يَنْفَعِلُ)",
        "pattern_past": "انْفَعَلَ",
        "pattern_present": "يَنْفَعِلُ",
        "verbal_noun": "انْفِعَال",
        "description": "Passive or reflexive of Form I; involuntary action (e.g. انْقَلَبَ 'he turned around').",
        "regex_template": r"^ان{r1}{r2}{r3}$",
    },
    {
        "form": 8,
        "name": "Form VIII (افْتَعَلَ / يَفْتَعِلُ)",
        "pattern_past": "افْتَعَلَ",
        "pattern_present": "يَفْتَعِلُ",
        "verbal_noun": "افْتِعَال",
        "description": "Reflexive, earnest endeavor, or middle voice (e.g. اكْتَسَبَ 'he earned for himself').",
        "regex_template": r"^ا{r1}ت{r2}{r3}$",
    },
    {
        "form": 9,
        "name": "Form IX (افْعَلَّ / يَفْعَلُّ)",
        "pattern_past": "افْعَلَّ",
        "pattern_present": "يَفْعَلُّ",
        "verbal_noun": "افْعِلَال",
        "description": "Acquiring a color or physical defect (e.g. اصْفَرَّ 'it became yellow').",
        "regex_template": r"^ا{r1}{r2}{r3}{r3}$",
    },
    {
        "form": 10,
        "name": "Form X (اسْتَفْعَلَ / يَسْتَفْعِلُ)",
        "pattern_past": "اسْتَفْعَلَ",
        "pattern_present": "يَسْتَفْعِلُ",
        "verbal_noun": "اسْتِفْعَال",
        "description": "Seeking, requesting, or deeming an action (e.g. اسْتَغْفَرَ 'he sought forgiveness', اسْتَعَانَ 'he sought help').",
        "regex_template": r"^است{r1}{r2}{r3}$",
    },
]

PROCLITICS = [
    ("وال", "and the", "CONJ+DET"),
    ("فال", "so the", "CONJ+DET"),
    ("بال", "with the", "P+DET"),
    ("كال", "like the", "P+DET"),
    ("لل", "for the", "P+DET"),
    ("ال", "the", "DET"),
    ("و", "and", "CONJ"),
    ("ف", "then/so", "CONJ"),
    ("ب", "in/by/with", "P"),
    ("ل", "for/to/indeed", "P"),
    ("ك", "as/like", "P"),
    ("س", "will (future)", "FUT"),
]

ENCLITICS = [
    ("هما", "them (dual)", "PRON"),
    ("هم", "them (masc. pl.)", "PRON"),
    ("هن", "them (fem. pl.)", "PRON"),
    ("كما", "you both", "PRON"),
    ("كم", "you all (masc.)", "PRON"),
    ("كن", "you all (fem.)", "PRON"),
    ("نا", "us / our", "PRON"),
    ("ني", "me", "PRON"),
    ("ها", "her / it", "PRON"),
    ("ه", "him / it", "PRON"),
    ("ك", "you (sing.)", "PRON"),
    ("ي", "my", "PRON"),
]


def strip_tashkeel(text: str) -> str:
    """Removes all Arabic short vowels, sukun, shaddah, and Quranic recitation marks."""
    return TASHKEEL_REGEX.sub("", text)


def normalize_arabic(text: str) -> str:
    """Normalizes variant alef forms, ya/alif maqsura, and ta marbuta for robust matching."""
    cleaned = strip_tashkeel(text)
    cleaned = re.sub(r"[إأآٱ]", "ا", cleaned)
    cleaned = re.sub(r"ة", "ه", cleaned)
    cleaned = re.sub(r"ى", "ي", cleaned)
    return cleaned.strip()


class MorphologyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def segment_clitics(self, word_raw: str) -> dict[str, Any]:
        """Segments proclitics (prefixes) and enclitics (suffixes) from an Arabic word token."""
        normalized = normalize_arabic(word_raw)
        detected_prefix: dict[str, str] | None = None
        detected_suffix: dict[str, str] | None = None
        stem = normalized

        # 1. Match longest prefix
        for prefix, meaning, p_type in sorted(PROCLITICS, key=lambda x: len(x[0]), reverse=True):
            if stem.startswith(prefix) and len(stem) > len(prefix) + 2:
                detected_prefix = {"clitic": prefix, "meaning": meaning, "type": p_type}
                stem = stem[len(prefix) :]
                break

        # 2. Match longest suffix
        for suffix, meaning, s_type in sorted(ENCLITICS, key=lambda x: len(x[0]), reverse=True):
            if stem.endswith(suffix) and len(stem) > len(suffix) + 2:
                detected_suffix = {"clitic": suffix, "meaning": meaning, "type": s_type}
                stem = stem[: -len(suffix)]
                break

        return {
            "original": word_raw,
            "normalized": normalized,
            "prefix": detected_prefix,
            "stem": stem,
            "suffix": detected_suffix,
        }

    async def analyze_word(self, word_raw: str) -> dict[str, Any]:
        """Performs multi-layered morphological analysis: clitic segmentation,

        database lemma & root verification, and pattern matching.
        """
        logger.debug("Analyzing morphology for word: %s", word_raw)
        segmentation = self.segment_clitics(word_raw)
        norm = segmentation["normalized"]
        stem = segmentation["stem"]

        # Search for exact word or stem in the Quranic word dictionary
        stmt = (
            select(Word)
            .where(
                (Word.text_imlaei == norm)
                | (Word.text_imlaei == stem)
                | (Word.text_uthmani == word_raw)
            )
            .limit(5)
        )
        res = await self.db.execute(stmt)
        matched_words = res.scalars().all()

        root = None
        lemma = None
        pos_tag = None

        if matched_words:
            # Pick first match with root populated
            for mw in matched_words:
                if mw.root:
                    root = mw.root
                    lemma = mw.lemma
                    pos_tag = mw.pos_tag
                    break
            if not root:
                root = matched_words[0].root
                lemma = matched_words[0].lemma
                pos_tag = matched_words[0].pos_tag

        detected_form = None
        if root and len(root) == 3:
            detected_form = self._detect_verb_form(stem, root)

        return {
            "word": word_raw,
            "normalized": norm,
            "segmentation": segmentation,
            "root": root,
            "lemma": lemma,
            "pos_tag": pos_tag,
            "detected_form": detected_form,
            "is_quranic": len(matched_words) > 0,
        }

    def _detect_verb_form(self, stem: str, root: str) -> dict[str, Any] | None:
        """Determines if the stem corresponds to any of the 10 Classical Arabic verb forms."""
        r1, r2, r3 = root[0], root[1], root[2]
        for form_info in VERB_FORMS_CATALOG:
            regex_pat = form_info["regex_template"].format(r1=r1, r2=r2, r3=r3)
            if re.match(regex_pat, stem):
                return {
                    "form_number": form_info["form"],
                    "name": form_info["name"],
                    "pattern_past": form_info["pattern_past"],
                    "pattern_present": form_info["pattern_present"],
                    "verbal_noun": form_info["verbal_noun"],
                    "description": form_info["description"],
                }
        return None

    async def get_root_concordance(self, root: str) -> dict[str, Any]:
        """Fetches all occurrences, distinct lemmas, and verse references for an Arabic root."""
        clean_root = normalize_arabic(root)
        logger.info("Fetching root concordance for root=%s", clean_root)

        # 1. Total occurrences
        count_stmt = select(func.count(Word.id)).where(Word.root == clean_root)
        count_res = await self.db.execute(count_stmt)
        total_occurrences = count_res.scalar() or 0

        # 2. Distinct lemmas derived from this root
        lemma_stmt = (
            select(Word.lemma, func.count(Word.id).label("count"))
            .where(Word.root == clean_root, Word.lemma.is_not(None))
            .group_by(Word.lemma)
            .order_by(func.count(Word.id).desc())
        )
        lemma_res = await self.db.execute(lemma_stmt)
        lemmas = [{"lemma": row[0], "count": row[1]} for row in lemma_res.all()]

        # 3. Sample Quranic citations
        citations_stmt = (
            select(Word, Verse, Surah)
            .join(Verse, Word.verse_id == Verse.id)
            .join(Surah, Verse.surah_id == Surah.id)
            .where(Word.root == clean_root)
            .limit(10)
        )
        cit_res = await self.db.execute(citations_stmt)
        citations = []
        for word_row, verse_row, surah_row in cit_res.all():
            citations.append(
                {
                    "surah_number": surah_row.number,
                    "surah_name": surah_row.name_transliteration,
                    "surah_name_arabic": surah_row.name_arabic,
                    "ayah_number": verse_row.ayah_number,
                    "word_position": word_row.position,
                    "word_text": word_row.text_uthmani,
                    "verse_text": verse_row.text_uthmani,
                    "verse_translation_en": verse_row.translation_en,
                }
            )

        return {
            "root": clean_root,
            "total_occurrences": total_occurrences,
            "distinct_lemmas": lemmas,
            "citations": citations,
        }

    def list_verb_forms(self) -> list[dict[str, Any]]:
        """Returns the educational reference catalog of all 10 Classical Arabic verb forms."""
        return [
            {
                "form_number": f["form"],
                "name": f["name"],
                "pattern_past": f["pattern_past"],
                "pattern_present": f["pattern_present"],
                "verbal_noun": f["verbal_noun"],
                "description": f["description"],
            }
            for f in VERB_FORMS_CATALOG
        ]
