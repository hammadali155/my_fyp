package com.meher.jawhar.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Shapes
import androidx.compose.material3.Typography
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

private val AppleLightColorScheme = lightColorScheme(
    primary = AppleEmerald,
    onPrimary = AppleSysCard,
    primaryContainer = AppleEmeraldMuted,
    onPrimaryContainer = AppleEmerald,
    secondary = AppleGold,
    onSecondary = AppleSysCard,
    secondaryContainer = AppleGoldLight,
    onSecondaryContainer = AppleTextPrimary,
    background = AppleSysBackground,
    onBackground = AppleTextPrimary,
    surface = AppleSysCard,
    onSurface = AppleTextPrimary,
    surfaceVariant = AppleSysCardSecondary,
    onSurfaceVariant = AppleTextSecondary,
    outline = AppleSysBorder,
    outlineVariant = AppleSysBorderSubtle,
)

private val AppleDarkColorScheme = darkColorScheme(
    primary = AppleEmeraldDark,
    onPrimary = AppleSysDarkBackground,
    primaryContainer = AppleSysDarkCardSecondary,
    onPrimaryContainer = AppleEmeraldDark,
    secondary = AppleGoldDark,
    onSecondary = AppleSysDarkBackground,
    secondaryContainer = AppleSysDarkCardSecondary,
    onSecondaryContainer = AppleDarkTextPrimary,
    background = AppleSysDarkBackground,
    onBackground = AppleDarkTextPrimary,
    surface = AppleSysDarkCard,
    onSurface = AppleDarkTextPrimary,
    surfaceVariant = AppleSysDarkCardSecondary,
    onSurfaceVariant = AppleDarkTextSecondary,
    outline = AppleSysDarkBorder,
    outlineVariant = AppleSysDarkBorderSubtle,
)

// Apple HIG Smooth Continuous Radii
val AppleShapes = Shapes(
    extraSmall = RoundedCornerShape(6.dp),
    small = RoundedCornerShape(10.dp),
    medium = RoundedCornerShape(16.dp),
    large = RoundedCornerShape(22.dp),
    extraLarge = RoundedCornerShape(32.dp),
)

// Apple HIG Typographic Hierarchy
val AppleTypography = Typography(
    displayLarge = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.Bold,
        fontSize = 34.sp,
        lineHeight = 41.sp,
    ),
    headlineLarge = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.Bold,
        fontSize = 28.sp,
        lineHeight = 34.sp,
    ),
    headlineMedium = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.SemiBold,
        fontSize = 22.sp,
        lineHeight = 28.sp,
    ),
    titleLarge = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.SemiBold,
        fontSize = 20.sp,
        lineHeight = 25.sp,
    ),
    titleMedium = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.SemiBold,
        fontSize = 17.sp,
        lineHeight = 22.sp,
    ),
    bodyLarge = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.Normal,
        fontSize = 17.sp,
        lineHeight = 24.sp,
    ),
    bodyMedium = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.Normal,
        fontSize = 15.sp,
        lineHeight = 20.sp,
    ),
    bodySmall = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.Normal,
        fontSize = 13.sp,
        lineHeight = 18.sp,
    ),
    labelLarge = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.Medium,
        fontSize = 14.sp,
        lineHeight = 18.sp,
    ),
    labelSmall = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.Medium,
        fontSize = 11.sp,
        lineHeight = 14.sp,
        letterSpacing = 0.5.sp,
    ),
)

@Composable
fun JawharTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit,
) {
    val colorScheme = if (darkTheme) AppleDarkColorScheme else AppleLightColorScheme

    MaterialTheme(
        colorScheme = colorScheme,
        shapes = AppleShapes,
        typography = AppleTypography,
        content = content,
    )
}
