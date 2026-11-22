package com.meher.jawhar.data.api

import io.ktor.client.HttpClient
import io.ktor.client.engine.darwin.Darwin
import io.ktor.client.plugins.contentnegotiation.ContentNegotiation
import io.ktor.client.request.get
import io.ktor.serialization.kotlinx.json.json

actual fun createHttpClient(): HttpClient = HttpClient(Darwin) {
    install(ContentNegotiation) { json(apiJson) }
}

actual fun defaultApiBaseUrl(): String = "http://localhost:8000"

actual suspend fun probeLocalBackend(timeoutMs: Int): Boolean {
    return try {
        val client = HttpClient(Darwin) {
            install(ContentNegotiation) { json(apiJson) }
        }
        val resp = client.get("${defaultApiBaseUrl()}/health/live")
        resp.status.value == 200
    } catch (e: Exception) {
        false
    }
}

actual fun renderApiBaseUrl(): String = "https://jawhar-backend.onrender.com"
