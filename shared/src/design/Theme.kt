package com.meher.jawhar.design

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.ReadOnlyComposable
import androidx.compose.runtime.compositionLocalOf
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp

val LocalJawharColors = staticCompositionLocalOf { JawharLightColors }
val LocalJawharType = staticCompositionLocalOf { DefaultJawharType }
val LocalTopInset = compositionLocalOf { 0.dp }
val LocalBottomInset = compositionLocalOf { 0.dp }

object Jawhar {
    val colors: JawharColors
        @Composable @ReadOnlyComposable get() = LocalJawharColors.current

    val type: JawharType
        @Composable @ReadOnlyComposable get() = LocalJawharType.current
}

@Composable
fun JawharTheme(
    dark: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit,
) {
    val c = if (dark) JawharDarkColors else JawharLightColors
    val type = rememberJawharType()
    val scheme = if (dark) {
        darkColorScheme(
            primary = c.primary, onPrimary = c.onPrimary, primaryContainer = c.primaryContainer,
            onPrimaryContainer = c.onPrimaryContainer, secondary = c.accent, onSecondary = c.onAccent,
            background = c.bgBase, onBackground = c.onSurface, surface = c.bgSurface, onSurface = c.onSurface,
            surfaceVariant = c.bgSurfaceVariant, onSurfaceVariant = c.onSurfaceVariant, error = c.error,
            outline = c.outline, outlineVariant = c.outlineVariant,
        )
    } else {
        lightColorScheme(
            primary = c.primary, onPrimary = c.onPrimary, primaryContainer = c.primaryContainer,
            onPrimaryContainer = c.onPrimaryContainer, secondary = c.accent, onSecondary = c.onAccent,
            background = c.bgBase, onBackground = c.onSurface, surface = c.bgSurface, onSurface = c.onSurface,
            surfaceVariant = c.bgSurfaceVariant, onSurfaceVariant = c.onSurfaceVariant, error = c.error,
            outline = c.outline, outlineVariant = c.outlineVariant,
        )
    }
    CompositionLocalProvider(LocalJawharColors provides c, LocalJawharType provides type) {
        MaterialTheme(colorScheme = scheme, content = content)
    }
}
