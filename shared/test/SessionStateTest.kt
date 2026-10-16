package com.meher.jawhar.nav

import com.meher.jawhar.data.api.SrsCardDto
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertNull
import kotlin.test.assertTrue

class SessionStateTest {
    private fun card(id: Int) = SrsCardDto(id = id, item_type = "word", front = "كَتَبَ", back = "wrote", state = "review")

    @Test
    fun firstSurahEntersAndSwitches() {
        val r = ReaderState()
        assertTrue(r.enterSurah(1, "Al-Fatiha"), "first entry should switch")
        assertEquals("Al-Fatiha", r.surahName)
        assertTrue(r.loading)
    }

    @Test
    fun reenteringSameSurahKeepsYourPlace() {
        val r = ReaderState()
        r.enterSurah(2, "Al-Baqarah")
        r.popup = true
        assertFalse(r.enterSurah(2, "Al-Baqarah"), "same surah must not reset")
        assertTrue(r.popup, "word popup should survive leaving and returning")
    }

    @Test
    fun switchingSurahClearsTheOldSession() {
        val r = ReaderState()
        r.enterSurah(1, "Al-Fatiha")
        r.popup = true
        assertTrue(r.enterSurah(3, "Ali 'Imran"), "a different surah must reset")
        assertFalse(r.popup, "popup belongs to the old surah")
        assertTrue(r.loading)
        assertEquals("Ali 'Imran", r.surahName)
    }

    @Test
    fun reviewQueueIsFetchedOnceAndSurvivesReturn() {
        val rv = ReviewState()
        rv.enter(listOf(card(1), card(2)), showBack = false)
        rv.reveal()
        rv.advance()
        assertEquals(1, rv.index)
        assertEquals(2, rv.card?.id)

        rv.enter(emptyList(), showBack = false)
        assertEquals(2, rv.queue.size, "re-entering must not wipe the queue")
        assertEquals(1, rv.index, "re-entering must not rewind")
        assertFalse(rv.back, "a new card starts face down")
    }

    @Test
    fun advanceRevealsThenMoves() {
        val rv = ReviewState()
        rv.enter(listOf(card(1), card(2)), showBack = false)
        assertFalse(rv.back)
        rv.reveal()
        assertTrue(rv.back)
        rv.advance()
        assertFalse(rv.back, "advance must hide the answer for the next card")
        assertEquals(1, rv.index)
    }

    @Test
    fun emptyQueueHasNoCard() {
        val rv = ReviewState()
        rv.enter(emptyList(), showBack = false)
        assertNull(rv.card)
    }
}