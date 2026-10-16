package com.meher.jawhar.nav

import androidx.compose.foundation.ScrollState
import androidx.compose.runtime.compositionLocalOf
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import com.meher.jawhar.data.api.SrsCardDto
import com.meher.jawhar.data.api.VerseDto
import com.meher.jawhar.data.api.WordDto

class ReaderState {
    var loadedSurah: Int? = null
        private set

    var surahName by mutableStateOf("Al-Fatiha")
    var verses by mutableStateOf<List<VerseDto>>(emptyList())
    var loading by mutableStateOf(false)
    var failed by mutableStateOf(false)
    var selectedWord by mutableStateOf<WordDto?>(null)
    var popup by mutableStateOf(false)
    val scroll = ScrollState(0)

    fun enterSurah(id: Int, name: String): Boolean {
        if (loadedSurah == id) return false
        loadedSurah = id
        surahName = name
        verses = emptyList()
        selectedWord = null
        popup = false
        failed = false
        loading = true
        return true
    }
}

class ReviewState {
    var queue by mutableStateOf<List<SrsCardDto>>(emptyList())
        private set
    var index by mutableStateOf(0)
        private set
    var back by mutableStateOf(false)
    var loading by mutableStateOf(false)

    val card: SrsCardDto? get() = queue.getOrNull(index)

    fun enter(cards: List<SrsCardDto>, showBack: Boolean) {
        if (queue.isNotEmpty()) {
            back = showBack
            return
        }
        queue = cards
        back = showBack
    }

    fun reveal() {
        back = true
    }

    fun advance() {
        back = false
        index++
    }
}

class ScreenSession {
    val reader = ReaderState()
    val review = ReviewState()
}

val LocalSession = compositionLocalOf { ScreenSession() }