package com.meher.jawhar.data

import androidx.compose.runtime.compositionLocalOf
import com.meher.jawhar.data.api.ApiClient
import com.meher.jawhar.data.api.Session

val LocalApi = compositionLocalOf { ApiClient() }

object AppState {
    val api = ApiClient()
    var galleryEnabled: Boolean = false
    var activeSurahId: Int = 1
    var activeSurahName: String = "Al-Fatiha"

    fun isLoggedIn(): Boolean = Session.accessToken != null

    fun logout() {
        Session.accessToken = null
        Session.refreshToken = null
        Session.userName = null
    }
}

