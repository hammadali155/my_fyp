package com.meher.jawhar.data.api

import kotlinx.serialization.Serializable
import kotlinx.serialization.json.JsonElement

@Serializable
data class SurahDto(
    val id: Int,
    val number: Int,
    val name_arabic: String,
    val name_transliteration: String,
    val name_english: String,
    val revelation_place: String? = null,
    val verse_count: Int,
)

@Serializable
data class WordDto(
    val id: Int,
    val position: Int,
    val text_uthmani: String,
    val text_imlaei: String? = null,
    val translation_en: String? = null,
    val transliteration: String? = null,
    val root: String? = null,
    val lemma: String? = null,
    val pos_tag: String? = null,
    val pattern: String? = null,
    val tense: String? = null,
    val voice: String? = null,
    val gender: String? = null,
    val number: String? = null,
    val person: String? = null,
    val features_json: Map<String, JsonElement>? = null,
)

@Serializable
data class VerseDto(
    val id: Int,
    val surah_id: Int,
    val ayah_number: Int,
    val text_uthmani: String,
    val text_imlaei: String? = null,
    val translation_en: String? = null,
    val translation_ur: String? = null,
    val words: List<WordDto> = emptyList(),
)

@Serializable
data class SurahListDto(val items: List<SurahDto>, val total: Int)

@Serializable
data class VerseListDto(val items: List<VerseDto>, val total: Int, val surah: SurahDto? = null)

@Serializable
data class AnalyzeRequestDto(val word: String)

@Serializable
data class AnalyzeResponseDto(
    val word: String,
    val normalized: String? = null,
    val root: String? = null,
    val lemma: String? = null,
    val pos_tag: String? = null,
    val pattern: String? = null,
    val source: String? = null,
    val is_quranic: Boolean? = null,
)

@Serializable
data class SegmentationDto(val original: String, val normalized: String, val stem: String)

@Serializable
data class LoginRequestDto(val email: String, val password: String)

@Serializable
data class TokenDto(
    val access_token: String,
    val refresh_token: String,
    val token_type: String = "bearer",
    val expires_in: Int = 0,
)

@Serializable
data class AuthResponseDto(val user: UserDto, val tokens: TokenDto)

@Serializable
data class UserDto(
    val id: Int,
    val email: String,
    val name: String,
    val level: String? = null,
    val streak_days: Int = 0,
    val xp: Int = 0,
    val created_at: String? = null,
)

@Serializable
data class SrsCardDto(
    val id: Int,
    val item_type: String,
    val front: String,
    val back: String,
    val hint: String? = null,
    val word_id: Int? = null,
    val state: String,
    val new_card: Boolean = false,
    val word_root: String? = null,
    val word_pattern: String? = null,
    val word_pos_tag: String? = null,
    val transliteration: String? = null,
    val example_surah_number: Int? = null,
    val example_ayah_number: Int? = null,
    val example_ayah_text: String? = null,
    val example_ayah_translation: String? = null,
)

@Serializable
data class SrsDueDto(
    val cards: List<SrsCardDto> = emptyList(),
    val total: Int = 0,
    val new_count: Int = 0,
    val learning_count: Int = 0,
    val review_count: Int = 0,
)

@Serializable
data class SrsReviewRequestDto(val card_id: Int, val rating: Int, val review_duration_ms: Int? = null)

@Serializable
data class SrsReviewResponseDto(val card_id: Int, val new_state: String, val new_interval_days: Int, val new_ease_factor: Float, val next_due: String)

@Serializable
data class SrsStatsDto(val total_cards: Int, val new_cards: Int, val learning_cards: Int, val review_cards: Int, val graduated_cards: Int, val reviews_today: Int, val streak_days: Int, val due_now: Int)

@Serializable
data class DeckStateCountsDto(val new: Int = 0, val learning: Int = 0, val review: Int = 0, val graduated: Int = 0)

@Serializable
data class DeckDto(
    val id: Int,
    val name: String,
    val is_default: Boolean = false,
    val counts: DeckStateCountsDto = DeckStateCountsDto(),
    val total_cards: Int = 0,
) {
    val card_count: Int get() = total_cards
    val due_count: Int get() = counts.new + counts.learning + counts.review
}

@Serializable
data class DeckListDto(val items: List<DeckDto>, val total: Int)

@Serializable
data class QuranSearchResponseDto(val query: String, val total: Int, val items: List<SearchItemDto>)

@Serializable
data class SearchItemDto(
    val surah_number: Int,
    val surah_name_english: String,
    val ayah_number: Int,
    val text_uthmani: String,
    val translation_en: String? = null,
    val translation_ur: String? = null,
    val matched_field: String? = null,
)

@Serializable
data class RootRankResponseDto(val items: List<RootRankItemDto>, val total: Int)

@Serializable
data class RootRankItemDto(val root: String, val occurrence_count: Int)

@Serializable
data class ConjugateResponseDto(
    val root: String,
    val form: Int,
    val supported: Boolean,
    val unsupported_reason: String? = null,
    val past: String? = null,
    val present: String? = null,
    val imperative: String? = null,
    val verbal_noun_pattern: String? = null,
    val form_name: String? = null,
)

@Serializable
data class WordFamilyResponseDto(val root: String, val total_occurrences: Int, val groups: List<WordFamilyGroupDto>)

@Serializable
data class WordFamilyGroupDto(val pos_tag: String? = null, val lemma: String? = null, val count: Int, val example: PatternExampleDto? = null)

@Serializable
data class PatternExampleDto(val surah_number: Int, val ayah_number: Int, val word_position: Int, val word_text: String, val lemma: String? = null)

@Serializable
data class PatternsResponseDto(val verb_forms: List<VerbFormDto>, val noun_patterns: List<NounPatternDto>)

@Serializable
data class VerbFormDto(val form_number: Int, val name: String, val pattern_past: String, val pattern_present: String, val verbal_noun: String, val description: String)

@Serializable
data class NounPatternDto(val pattern: String, val name: String, val example: PatternExampleDto? = null)

@Serializable
data class BadgeDto(
    val slug: String,
    val label: String,
    val icon: String? = null,
    val earned: Boolean,
    val earned_at: String? = null,
) {
    val name: String get() = label
    val description: String get() = slug.replace("_", " ").replaceFirstChar { it.uppercase() }
    val unlocked: Boolean get() = earned
}

@Serializable
data class BadgeListResponseDto(val items: List<BadgeDto>, val total: Int, val earned_count: Int)

@Serializable
data class ConjugateRequestDto(val root: String, val form: Int)

@Serializable
data class RegisterRequestDto(
    val email: String,
    val name: String,
    val password: String,
    val native_lang: String = "en",
    val ui_lang: String = "en",
    val level: String = "beginner",
)

@Serializable
data class RefreshTokenRequestDto(val refresh_token: String)

@Serializable
data class UserUpdateRequestDto(
    val name: String? = null,
    val native_lang: String? = null,
    val ui_lang: String? = null,
    val level: String? = null,
    val learning_goal: String? = null,
)

@Serializable
data class MessageResponseDto(val message: String)

// ---------- Bookmarks ----------

@Serializable
data class BookmarkCreateDto(val verse_id: Int, val note: String? = null, val collection: String? = null)

@Serializable
data class BookmarkResponseDto(
    val id: Int,
    val verse_id: Int,
    val note: String? = null,
    val collection: String? = null,
    val created_at: String,
    val updated_at: String,
    val surah_number: Int? = null,
    val ayah_number: Int? = null,
)

@Serializable
data class BookmarkListResponseDto(val items: List<BookmarkResponseDto>, val total: Int)

// ---------- Decks ----------

@Serializable
data class DeckCreateDto(val name: String)

@Serializable
data class AddWordRequestDto(val word_id: Int)

@Serializable
data class BulkAddWordsRequestDto(val word_ids: List<Int>)

@Serializable
data class DeckWordAddResponseDto(val added: Int, val skipped_duplicates: Int, val card_ids: List<Int>)

// ---------- Morphology (extra fields not in existing DTOs) ----------

@Serializable
data class CliticDetailDto(val clitic: String, val meaning: String, val type: String)

@Serializable
data class SegmentationDetailDto(
    val original: String,
    val normalized: String,
    val prefix: CliticDetailDto?,
    val stem: String,
    val suffix: CliticDetailDto?,
)

@Serializable
data class MorphologyAnalyzeResponseDto(
    val word: String,
    val normalized: String,
    val segmentation: SegmentationDetailDto?,
    val root: String?,
    val lemma: String?,
    val pos_tag: String?,
    val detected_form: VerbFormDto?,
    val is_quranic: Boolean,
    val source: String?,
    val pattern: String?,
    val features_json: Map<String, JsonElement>?,
)

@Serializable
data class LemmaCountDto(val lemma: String, val count: Int)

@Serializable
data class RootCitationDto(
    val surah_number: Int,
    val surah_name: String,
    val surah_name_arabic: String,
    val ayah_number: Int,
    val word_position: Int,
    val word_text: String,
    val verse_text: String,
    val verse_translation_en: String?,
)

@Serializable
data class RootConcordanceResponseDto(
    val root: String,
    val total_occurrences: Int,
    val distinct_lemmas: List<LemmaCountDto>,
    val citations: List<RootCitationDto>,
)

// ---------- Nahw ----------

@Serializable
data class NahwTokenDto(
    val position: Int,
    val text_uthmani: String,
    val role_ar: String?,
    val role_en: String,
    val role_key: String,
    val dep_type: String?,
    val irab: String?,
    val head_index: Int?,
    val head_surah_number: Int?,
    val head_ayah_number: Int?,
    val sentence_index: Int?,
)

@Serializable
data class NahwVerseResponseDto(
    val surah_number: Int,
    val ayah_number: Int,
    val tokens: List<NahwTokenDto>,
    val has_annotations: Boolean = false,
    val message: String? = null,
)

@Serializable
data class NahwParseRequestDto(val text: String, val is_quranic: Boolean = false)

@Serializable
data class NahwParseResponseDto(val source: String, val tokens: List<NahwTokenDto>)

@Serializable
data class WordMorphologyDto(
    val text_uthmani: String,
    val text_imlaei: String?,
    val root: String?,
    val lemma: String?,
    val pos_tag: String?,
    val pattern: String?,
    val tense: String?,
    val voice: String?,
    val gender: String?,
    val number: String?,
    val person: String?,
    val features_json: Map<String, JsonElement>?,
)

@Serializable
data class TreebankRelationDto(
    val role: String?,
    val dep_type: String?,
    val head_index: Int?,
    val head_surah_number: Int?,
    val head_ayah_number: Int?,
    val irab: String?,
    val sentence_index: Int?,
)

@Serializable
data class ExplainGroundingDto(
    val word_id: Int,
    val position: Int,
    val surah_number: Int,
    val ayah_number: Int,
    val verse_text: String,
    val translation: String?,
    val morphology: WordMorphologyDto,
    val relation: TreebankRelationDto?,
    val missing_data: List<String> = emptyList(),
)

@Serializable
data class NahwExplainResponseDto(
    val word_id: Int,
    val language: String,
    val source: String,
    val explanation: String,
    val cached: Boolean = false,
    val grounding: ExplainGroundingDto,
)

// ---------- Tutor ----------

@Serializable
data class TutorReferenceDto(
    val surah_number: Int?,
    val ayah_number: Int?,
    val word_id: Int?,
)

@Serializable
data class TutorChatRequestDto(
    val message: String,
    val session_id: Int?,
    val reference: TutorReferenceDto?,
)

@Serializable
data class TutorCitationOutDto(val surah: Int, val ayah: Int)

@Serializable
data class TutorUsageDto(val prompt_tokens: Int?, val completion_tokens: Int?)

@Serializable
data class TutorChatResponseDto(
    val session_id: Int,
    val reply: String,
    val citations: List<TutorCitationOutDto>,
    val model: String,
    val usage: TutorUsageDto,
    val truncated_context: Boolean = false,
    val unresolved_references: List<String> = emptyList(),
    val incomplete: Boolean = false,
)

@Serializable
data class TutorSessionSummaryDto(
    val id: Int,
    val title: String,
    val message_count: Int,
    val created_at: String,
    val updated_at: String,
)

@Serializable
data class TutorSessionListDto(val sessions: List<TutorSessionSummaryDto>)

// ---------- Health ----------

@Serializable
data class ComponentHealthDto(val status: String, val latency_ms: Double?, val error: String?)

@Serializable
data class HealthResponseDto(
    val status: String,
    val version: String,
    val uptime_seconds: Double,
    val timestamp: String,
    val environment: String,
    val python_version: String,
    val platform: String,
    val database: ComponentHealthDto,
)

@Serializable
data class SimpleProbeResponseDto(val status: String)
