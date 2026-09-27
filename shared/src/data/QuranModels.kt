package com.meher.jawhar.data

data class Surah(
    val id: Int,
    val number: Int,
    val nameArabic: String,
    val nameTransliteration: String,
    val nameEnglish: String,
    val revelationPlace: String?,
    val verseCount: Int,
)

data class Word(
    val id: Int,
    val position: Int,
    val textUthmani: String,
    val textImlaei: String? = null,
    val translationEn: String? = null,
    val transliteration: String? = null,
    val root: String? = null,
    val lemma: String? = null,
    val posTag: String? = null,
)

data class Verse(
    val id: Int,
    val surahId: Int,
    val ayahNumber: Int,
    val textUthmani: String,
    val textImlaei: String? = null,
    val translationEn: String? = null,
    val translationUr: String? = null,
    val words: List<Word> = emptyList(),
)
