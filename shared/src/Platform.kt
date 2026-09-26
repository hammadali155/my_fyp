package com.meher.jawhar

interface Platform {
    val name: String
}

expect fun getPlatform(): Platform
