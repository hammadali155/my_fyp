package com.meher.jawhar.data

import androidx.compose.runtime.compositionLocalOf
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import com.meher.jawhar.data.api.ApiClient
import com.meher.jawhar.data.api.Session

val LocalApi = compositionLocalOf { ApiClient() }

enum class ThemeMode { System, Light, Dark }

object AppState {
    val api = ApiClient()
    var galleryEnabled: Boolean = false
    var themeMode by mutableStateOf(ThemeMode.System)
    var isUsingLocalBackend by mutableStateOf(true)

    fun isLoggedIn(): Boolean = Session.accessToken != null

    fun logout() {
        Session.accessToken = null
        Session.refreshToken = null
        Session.userName = null
    }

    suspend fun resolveBackendUrl() {
        api.resolveBaseUrl()
        isUsingLocalBackend = api.isUsingLocalBackend
    }
}

