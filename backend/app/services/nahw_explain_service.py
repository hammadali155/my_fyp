from __future__ import annotations

from collections import OrderedDict

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.quran import NahwAnnotation, Surah, Verse, Word
from app.schemas.nahw import (
    ExplainGrounding,
    NahwExplainResponse,
    TreebankRelation,
    WordMorphology,
)
from app.services.llm_client import (
    ChatMessage,
    GenerationSettings,
    LLMClient,
    LLMError,
    LLMNotConfiguredError,
)

logger = get_logger("services.nahw_explain")

LANGUAGE_NAMES = {"en": "English", "ur": "Urdu"}
_EXPLANATION_CACHE_MAX = 512
_explanation_cache: OrderedDict[tuple[int, str], str] = OrderedDict()


def normalize_language(ui_lang: str | None) -> str:
    if ui_lang and ui_lang.lower().startswith("ur"):
        return "ur"
    return "en"


def clear_explanation_cache() -> None:
    _explanation_cache.clear()


def _cache_get(key: tuple[int, str]) -> str | None:
    value = _explanation_cache.get(key)
    if value is not None:
        _explanation_cache.move_to_end(key)
    return value


def _cache_put(key: tuple[int, str], value: str) -> None:
    _explanation_cache[key] = value
    _explanation_cache.move_to_end(key)
    while len(_explanation_cache) > _EXPLANATION_CACHE_MAX:
        _explanation_cache.popitem(last=False)


def build_explanation_system_prompt(language: str) -> str:
    language_name = LANGUAGE_NAMES.get(language, "English")
    return (
        "You are an expert Classical Arabic (Nahw) tutor. "
        f"Explain the grammar of ONE word in plain {language_name}.\n"
        "Rules:\n"
        "1. Use ONLY the data in the JSON block below. It comes from the Jawhar database.\n"
        "2. Do not add any grammar fact, meaning, root, case, or Quranic reference that is "
        "not in the data.\n"
        "3. If a field is null or listed in missing_data, say clearly that the data is "
        "unavailable. Do not guess. A head_index of -1 means there is no separate head "
        "word; a head_index of 0 means the head is an elided element; neither is a word "
        "position.\n"
        "4. Do not reproduce, complete, or generate Quranic text. The verse text is quoted "
        "verbatim from the database below.\n"
        "5. Do not cite any surah:ayah other than the one in the data.\n"
        "6. Keep the answer under 150 words."
    )


def build_explanation_message(grounding: ExplainGrounding) -> ChatMessage:
    return ChatMessage(
        role="user",
        content=(
            "Data (verbatim from the database):\n" + grounding.model_dump_json(indent=2)
        ),
    )


class NahwExplainService:
    def __init__(self, db: AsyncSession, client: LLMClient) -> None:
        self.db = db
        self.client = client

    async def explain(self, word_id: int, language: str) -> NahwExplainResponse:
        word, verse, surah = await self._load_word(word_id)
        annotation = await self._load_annotation(word_id)
        grounding = self._build_grounding(word, verse, surah, annotation, language)

        key = (word_id, language)
        cached_explanation = _cache_get(key)
        if cached_explanation is not None:
            logger.info("Served cached explanation word_id=%s language=%s", word_id, language)
            return self._response(word_id, language, cached_explanation, grounding, cached=True)

        prompt = build_explanation_system_prompt(language)
        message = build_explanation_message(grounding)
        try:
            result = await self.client.generate(
                system_prompt=prompt,
                messages=[message],
                settings=GenerationSettings(temperature=0.2, max_output_tokens=400),
            )
        except LLMNotConfiguredError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Explanation service is not configured (GEMINI_API_KEY is missing)",
            ) from exc
        except LLMError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Explanation service is unavailable; try again later",
            ) from exc

        explanation = result.text
        if not explanation.strip():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Explanation service returned an empty response",
            )

        _cache_put(key, explanation)
        logger.info("Generated explanation word_id=%s language=%s", word_id, language)
        return self._response(word_id, language, explanation, grounding, cached=False)

    async def _load_word(self, word_id: int) -> tuple[Word, Verse, Surah]:
        row = (
            await self.db.execute(
                select(Word, Verse, Surah)
                .join(Verse, Word.verse_id == Verse.id)
                .join(Surah, Verse.surah_id == Surah.id)
                .where(Word.id == word_id)
            )
        ).first()
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Word {word_id} not found",
            )
        word, verse, surah = row
        return word, verse, surah

    async def _load_annotation(self, word_id: int) -> NahwAnnotation | None:
        result = await self.db.execute(
            select(NahwAnnotation)
            .where(NahwAnnotation.word_id == word_id)
            .order_by(NahwAnnotation.id.asc())
        )
        return result.scalars().first()

    def _build_grounding(
        self,
        word: Word,
        verse: Verse,
        surah: Surah,
        annotation: NahwAnnotation | None,
        language: str,
    ) -> ExplainGrounding:
        translation = verse.translation_ur if language == "ur" else verse.translation_en
        morphology = WordMorphology(
            text_uthmani=word.text_uthmani,
            text_imlaei=word.text_imlaei,
            root=word.root,
            lemma=word.lemma,
            pos_tag=word.pos_tag,
            pattern=word.pattern,
            tense=word.tense,
            voice=word.voice,
            gender=word.gender,
            number=word.number,
            person=word.person,
            features_json=word.features_json,
        )
        relation = (
            TreebankRelation(
                role=annotation.role,
                dep_type=annotation.dep_type,
                head_index=annotation.head_index,
                head_surah_number=annotation.head_surah_number,
                head_ayah_number=annotation.head_ayah_number,
                irab=annotation.irab,
                sentence_index=annotation.sentence_index,
            )
            if annotation is not None
            else None
        )

        missing: list[str] = []
        if annotation is None:
            missing.append("treebank_relation")
        else:
            for name in ("role", "dep_type", "head_index", "irab"):
                if getattr(annotation, name) is None:
                    missing.append(f"treebank_{name}")
        for name in ("root", "lemma", "pos_tag"):
            if getattr(word, name) is None:
                missing.append(f"morphology_{name}")
        if translation is None:
            missing.append("translation")

        return ExplainGrounding(
            word_id=word.id,
            position=word.position,
            surah_number=surah.number,
            ayah_number=verse.ayah_number,
            verse_text=verse.text_uthmani,
            translation=translation,
            morphology=morphology,
            relation=relation,
            missing_data=missing,
        )

    def _response(
        self,
        word_id: int,
        language: str,
        explanation: str,
        grounding: ExplainGrounding,
        *,
        cached: bool,
    ) -> NahwExplainResponse:
        return NahwExplainResponse(
            word_id=word_id,
            language=language,
            source="gemini",
            explanation=explanation,
            cached=cached,
            grounding=grounding,
        )
