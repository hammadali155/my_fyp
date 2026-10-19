package com.meher.jawhar.nav

import androidx.compose.runtime.Composable

@Composable
actual fun SystemBackHandler(enabled: Boolean, onBack: () -> Unit) {
    // Desktop platform: back handled via UI navigation buttons
}
