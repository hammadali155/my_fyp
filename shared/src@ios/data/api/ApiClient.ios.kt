package com.meher.jawhar.data.api

import io.ktor.client.HttpClient
import io.ktor.client.engine.darwin.Darwin
import io.ktor.client.plugins.contentnegotiation.ContentNegotiation
import io.ktor.serialization.kotlinx.json.json

actual fun createHttpClient(): HttpClient = HttpClient(Darwin) {
    install(ContentNegotiation) { json(apiJson) }
}

actual fun defaultApiBaseUrl(): String = "http://localhost:8000"
