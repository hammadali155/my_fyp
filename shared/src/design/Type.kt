package com.meher.jawhar.design

import androidx.compose.runtime.Composable
import androidx.compose.runtime.Immutable
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.LineHeightStyle
import androidx.compose.ui.unit.sp
import com.meher.jawhar.resources.*
import org.jetbrains.compose.resources.Font

@Immutable
class JawharType(
    val displayL: TextStyle,
    val headlineL: TextStyle,
    val headlineM: TextStyle,
    val headlineS: TextStyle,
    val titleL: TextStyle,
    val titleM: TextStyle,
    val titleS: TextStyle,
    val bodyL: TextStyle,
    val bodyM: TextStyle,
    val bodyS: TextStyle,
    val labelL: TextStyle,
    val labelM: TextStyle,
    val labelS: TextStyle,
    val translit: TextStyle,
    val arabicQuranXL: TextStyle,
    val arabicQuranL: TextStyle,
    val arabicQuranM: TextStyle,
    val arabicWordXL: TextStyle,
    val arabicWordL: TextStyle,
    val arabicHeading: TextStyle,
    val arabicTitle: TextStyle,
    val arabicBody: TextStyle,
    val arabicLabel: TextStyle,
)

private val ArabicLineStyle = LineHeightStyle(
    alignment = LineHeightStyle.Alignment.Center,
    trim = LineHeightStyle.Trim.None,
)

fun buildJawharType(
    display: FontFamily,
    ui: FontFamily,
    translit: FontFamily,
    quran: FontFamily,
    wordBold: FontFamily,
    wordRegular: FontFamily,
    heading: FontFamily,
    arabicUi: FontFamily,
): JawharType {
    fun latin(family: FontFamily, weight: FontWeight, size: Int, line: Int, spacing: Float = 0f) = TextStyle(
        fontFamily = family,
        fontWeight = weight,
        fontSize = size.sp,
        lineHeight = line.sp,
        letterSpacing = spacing.sp,
    )

    fun arabic(family: FontFamily, weight: FontWeight, size: Int, line: Int) = TextStyle(
        fontFamily = family,
        fontWeight = weight,
        fontSize = size.sp,
        lineHeight = line.sp,
        lineHeightStyle = ArabicLineStyle,
    )

    return JawharType(
        displayL = latin(display, FontWeight.SemiBold, 40, 48, -0.5f),
        headlineL = latin(display, FontWeight.SemiBold, 32, 40, -0.3f),
        headlineM = latin(display, FontWeight.SemiBold, 26, 32, -0.2f),
        headlineS = latin(display, FontWeight.SemiBold, 22, 28),
        titleL = latin(ui, FontWeight.Bold, 18, 26),
        titleM = latin(ui, FontWeight.SemiBold, 16, 24),
        titleS = latin(ui, FontWeight.SemiBold, 14, 20),
        bodyL = latin(ui, FontWeight.Normal, 16, 24),
        bodyM = latin(ui, FontWeight.Normal, 14, 22),
        bodyS = latin(ui, FontWeight.Normal, 12, 18),
        labelL = latin(ui, FontWeight.SemiBold, 14, 20, 0.1f),
        labelM = latin(ui, FontWeight.SemiBold, 12, 16, 0.3f),
        labelS = latin(ui, FontWeight.Bold, 10, 14, 0.8f),
        translit = TextStyle(fontFamily = translit, fontStyle = FontStyle.Italic, fontSize = 16.sp, lineHeight = 24.sp),
        arabicQuranXL = arabic(quran, FontWeight.Normal, 44, 76),
        arabicQuranL = arabic(quran, FontWeight.Normal, 32, 58),
        arabicQuranM = arabic(quran, FontWeight.Normal, 26, 46),
        arabicWordXL = arabic(wordBold, FontWeight.Bold, 64, 96),
        arabicWordL = arabic(wordRegular, FontWeight.Normal, 40, 64),
        arabicHeading = arabic(heading, FontWeight.Bold, 28, 44),
        arabicTitle = arabic(arabicUi, FontWeight.SemiBold, 18, 30),
        arabicBody = arabic(arabicUi, FontWeight.Normal, 15, 26),
        arabicLabel = arabic(arabicUi, FontWeight.Medium, 13, 22),
    )
}

val DefaultJawharType: JawharType = buildJawharType(
    display = FontFamily.Serif,
    ui = FontFamily.SansSerif,
    translit = FontFamily.Serif,
    quran = FontFamily.Serif,
    wordBold = FontFamily.Serif,
    wordRegular = FontFamily.Serif,
    heading = FontFamily.Serif,
    arabicUi = FontFamily.SansSerif,
)

@Composable
fun rememberJawharType(): JawharType {
    val display = FontFamily(Font(Res.font.fraunces_semibold, FontWeight.SemiBold))
    val ui = FontFamily(
        Font(Res.font.plus_jakarta_sans_regular, FontWeight.Normal),
        Font(Res.font.plus_jakarta_sans_medium, FontWeight.Medium),
        Font(Res.font.plus_jakarta_sans_semibold, FontWeight.SemiBold),
        Font(Res.font.plus_jakarta_sans_bold, FontWeight.Bold),
    )
    val translit = FontFamily(Font(Res.font.newsreader_italic, FontWeight.Normal, FontStyle.Italic))
    val quran = FontFamily(Font(Res.font.amiri_quran_regular, FontWeight.Normal))
    val wordBold = FontFamily(Font(Res.font.scheherazade_new_bold, FontWeight.Bold))
    val wordRegular = FontFamily(Font(Res.font.scheherazade_new_regular, FontWeight.Normal))
    val heading = FontFamily(Font(Res.font.amiri_bold, FontWeight.Bold))
    val arabicUi = FontFamily(
        Font(Res.font.noto_sans_arabic_regular, FontWeight.Normal),
        Font(Res.font.noto_sans_arabic_medium, FontWeight.Medium),
        Font(Res.font.noto_sans_arabic_semibold, FontWeight.SemiBold),
    )
    return buildJawharType(display, ui, translit, quran, wordBold, wordRegular, heading, arabicUi)
}
