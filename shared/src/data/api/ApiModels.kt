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
data class TokenDto(val access_token: String, val refresh_token: String, val token_type: String = "bearer", val expires_in: Int = 0)

@Serializable
data class AuthResponseDto(val user: UserDto, val tokens: TokenDto)

@Serializable
data class UserDto(val id: Int, val email: String, val name: String, val level: String? = null)

@Serializable
data class SRSCardDto(
    val id: Int,
    val item_type: String,
    val front: String,
    val back: String,
    val hint: String? = null,
    val word_id: Int? = null,
    val surah_number: Int? = null,
    val ayah_number: Int? = null,
    val state: String,
)

@Serializable
data class SRSDueDto(val cards: List<SRSCardDto> = emptyList(), val total: Int = 0, val new_count: Int = 0, val learning_count: Int = 0, val review_count: Int = 0)

@Serializable
data class SRSReviewRequestDto(val card_id: Int, val rating: Int, val review_duration_ms: Int? = null)

@Serializable
data class SRSReviewResponseDto(val card_id: Int, val new_state: String, val new_interval_days: Int, val new_ease_factor: Float, val next_due: String)

@Serializable
data class SRSStatsDto(val total_cards: Int, val new_cards: Int, val learning_cards: Int, val review_cards: Int, val graduated_cards: Int, val reviews_today: Int, val streak_days: Int, val due_now: Int)

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
data class BadgeListResponseDto(val items: List<BadgeDto>, val total: Int, val earned_count: Int)

@Serializable
data class BadgeDto(val slug: String, val label: String, val icon: String? = null, val earned: Boolean, val earned_at: String? = null)

@Serializable
data class ConjugateRequestDto(val root: String, val form: Int)
