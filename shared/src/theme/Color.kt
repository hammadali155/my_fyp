package com.meher.jawhar.theme

import androidx.compose.ui.graphics.Color

// ==========================================
// Jawhar Apple-Inspired Design Tokens
// ==========================================

// Primary Accents (iOS Tint Colors)
val AppleEmerald = Color(0xFF0F766E)       // Refined iOS Teal-Emerald
val AppleEmeraldDark = Color(0xFF14B8A6)   // Vibrant Mint for Dark Mode
val AppleEmeraldMuted = Color(0xFFE6F4F1)  // Tinted background container
val AppleEmeraldSubtle = Color(0xFFF0FDF4)

val AppleGold = Color(0xFFD4AF37)          // Metallic Champagne Gold
val AppleGoldLight = Color(0xFFFEF9C3)     // Soft gold badge container
val AppleGoldDark = Color(0xFFFACC15)

// iOS System Colors (Light Mode)
val AppleSysBackground = Color(0xFFF2F2F7) // iOS System Grouped Background
val AppleSysCard = Color(0xFFFFFFFF)       // Inset Group Card / Material
val AppleSysCardSecondary = Color(0xFFF9FAFB)
val AppleSysBorder = Color(0xFFE5E7EB)     // Hairline separator (0.5dp)
val AppleSysBorderSubtle = Color(0x1A000000)

val AppleTextPrimary = Color(0xFF111827)   // High contrast near-black
val AppleTextSecondary = Color(0xFF6B7280) // Supporting caption text
val AppleTextTertiary = Color(0xFF9CA3AF)  // Placeholder / disabled text

// iOS System Colors (Dark Mode)
val AppleSysDarkBackground = Color(0xFF000000) // Pure OLED Black
val AppleSysDarkCard = Color(0xFF1C1C1E)       // Elevated Group Surface
val AppleSysDarkCardSecondary = Color(0xFF2C2C2E)
val AppleSysDarkBorder = Color(0xFF38383A)
val AppleSysDarkBorderSubtle = Color(0x33FFFFFF)

val AppleDarkTextPrimary = Color(0xFFFFFFFF)
val AppleDarkTextSecondary = Color(0xFF98989D)
val AppleDarkTextTertiary = Color(0xFF636366)

// Liquid Glass Translucencies
val AppleGlassLight = Color(0xE6FFFFFF)        // 90% opacity white with backdrop
val AppleGlassDark = Color(0xD91C1C1E)         // 85% opacity dark
val AppleGlassPill = Color(0x1F000000)
val AppleGlassPillDark = Color(0x33FFFFFF)

// Semantic Indicator Colors
val AppleSuccess = Color(0xFF34C759)
val AppleWarning = Color(0xFFFF9500)
val AppleDestructive = Color(0xFFFF3B30)
val AppleInfo = Color(0xFF007AFF)

// Compatibility aliases
val GoldAccent = AppleGold
val EmeraldForest = AppleEmerald
val EmeraldMedium = AppleEmeraldDark
val EmeraldLight = AppleEmeraldMuted
val EmeraldDeep = AppleEmerald
val SandBg = AppleSysBackground
val SandSurface = AppleSysCard
val SandBorder = AppleSysBorder
val InkPrimary = AppleTextPrimary
val InkSecondary = AppleTextSecondary
val InkMuted = AppleTextTertiary
val DarkBg = AppleSysDarkBackground
val DarkSurface = AppleSysDarkCard
val DarkBorder = AppleSysDarkBorder
val DarkTextPrimary = AppleDarkTextPrimary
val DarkTextSecondary = AppleDarkTextSecondary
