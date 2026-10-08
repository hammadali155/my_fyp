package com.meher.jawhar.data.api

import kotlinx.serialization.json.Json
import kotlin.test.Test
import kotlin.test.assertEquals

class ApiModelsTest {
    private val json = Json { ignoreUnknownKeys = true; isLenient = true }

    @Test
    fun parsesSurahList() {
        val raw = """{"items":[{"id":1,"number":1,"name_arabic":"الفاتحة","name_transliteration":"Al-Fatihah","name_english":"The Opener","revelation_place":"Makkah","verse_count":7}],"total":1}"""
        val dto = json.decodeFromString<SurahListDto>(raw)
        assertEquals(1, dto.total)
        assertEquals("Al-Fatihah", dto.items[0].name_transliteration)
    }

    @Test
    fun parsesAnalyzeResponseWithNewFields() {
        val raw = """{"word":"كتب","normalized":"كتب","root":"كتب","lemma":"كَتَبَ","pos_tag":"verb","pattern":"1َ2َ3َ","source":"camel","is_quranic":false}"""
        val dto = json.decodeFromString<AnalyzeResponseDto>(raw)
        assertEquals("كتب", dto.root)
        assertEquals("camel", dto.source)
    }

    @Test
    fun parsesSrsDue() {
        val raw = """{"cards":[{"id":1,"item_type":"vocabulary","front":"f","back":"b","hint":null,"word_id":1,"surah_number":1,"ayah_number":1,"state":"new"}],"total":1,"new_count":1,"learning_count":0,"review_count":0}"""
        val dto = json.decodeFromString<SRSDueDto>(raw)
        assertEquals(1, dto.total)
        assertEquals("new", dto.cards[0].state)
    }

    @Test
    fun parsesBadgeList() {
        val raw = """{"items":[{"slug":"first_review","label":"First Review","icon":"star","earned":true,"earned_at":null}],"total":1,"earned_count":1}"""
        val dto = json.decodeFromString<BadgeListResponseDto>(raw)
        assertEquals(1, dto.earned_count)
        assertEquals("first_review", dto.items[0].slug)
    }
}
