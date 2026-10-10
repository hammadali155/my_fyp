package com.meher.jawhar.data

import androidx.compose.runtime.compositionLocalOf
import com.meher.jawhar.data.api.ApiClient
import com.meher.jawhar.data.api.Session

val LocalApi = compositionLocalOf { ApiClient() }

object AppState {
    val api = ApiClient()

    fun isLoggedIn(): Boolean = Session.accessToken != null

    fun logout() {
        Session.accessToken = null
        Session.refreshToken = null
        Session.userName = null
    }
}
