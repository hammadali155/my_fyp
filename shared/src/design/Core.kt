package com.meher.jawhar.design

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.size
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.StrokeJoin
import androidx.compose.ui.graphics.Shape
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.drawscope.Fill
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.withTransform
import androidx.compose.ui.graphics.vector.PathParser
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlin.math.PI
import kotlin.math.cos
import kotlin.math.sin

@Composable
fun Modifier.tappable(enabled: Boolean = true, onClick: () -> Unit): Modifier = this.clickable(
    interactionSource = remember { MutableInteractionSource() },
    indication = null,
    enabled = enabled,
    onClick = onClick,
)

fun Modifier.softShadow(shape: Shape, elevation: Dp = 14.dp, alpha: Float = 0.28f): Modifier = this.shadow(
    elevation = elevation,
    shape = shape,
    clip = false,
    ambientColor = ShadowTint.copy(alpha = alpha),
    spotColor = ShadowTint.copy(alpha = alpha),
)

@Composable
fun JText(
    text: String,
    style: TextStyle,
    color: Color = Jawhar.colors.onSurface,
    modifier: Modifier = Modifier,
    textAlign: TextAlign? = null,
    maxLines: Int = Int.MAX_VALUE,
    overflow: TextOverflow = TextOverflow.Clip,
) {
    Text(
        text = text,
        style = style,
        color = color,
        modifier = modifier,
        textAlign = textAlign,
        maxLines = maxLines,
        overflow = overflow,
    )
}

@Composable
fun JArabic(
    text: String,
    style: TextStyle = Jawhar.type.arabicQuranM,
    color: Color = Jawhar.colors.onSurface,
    modifier: Modifier = Modifier,
    textAlign: TextAlign = TextAlign.Start,
) {
    CompositionLocalProvider(LocalLayoutDirection provides LayoutDirection.Rtl) {
        Text(text = text, style = style, color = color, modifier = modifier, textAlign = textAlign)
    }
}

@Composable
fun JIcon(
    icon: JI,
    modifier: Modifier = Modifier,
    size: Dp = 24.dp,
    tint: Color = Jawhar.colors.onSurface,
    strokeWidth: Dp = 1.8.dp,
    filled: Boolean = false,
) {
    val path = remember(icon) { PathParser().parsePathString(icon.path).toPath() }
    Canvas(modifier.size(size)) {
        val k = this.size.minDimension / 24f
        withTransform({ scale(k, k, pivot = Offset.Zero) }) {
            if (filled) {
                drawPath(path, tint, style = Fill)
            } else {
                drawPath(
                    path,
                    tint,
                    style = Stroke(width = strokeWidth.toPx() / k, cap = StrokeCap.Round, join = StrokeJoin.Round),
                )
            }
        }
    }
}

class StarSpec(val x: Dp, val y: Dp, val size: Dp, val alpha: Float = 0.2f)

private fun starPath(cx: Float, cy: Float, size: Float, inner: Float): Path {
    val r = size / 2f
    val p = Path()
    for (i in 0 until 16) {
        val ang = -PI / 2.0 + i * PI / 8.0
        val rad = if (i % 2 == 0) r else r * inner
        val x = cx + (rad * cos(ang)).toFloat()
        val y = cy + (rad * sin(ang)).toFloat()
        if (i == 0) p.moveTo(x, y) else p.lineTo(x, y)
    }
    p.close()
    return p
}

fun DrawScope.drawStarOutline(cx: Float, cy: Float, size: Float, color: Color, strokeWidth: Float) {
    drawPath(starPath(cx, cy, size, 0.72f), color, style = Stroke(width = strokeWidth, join = StrokeJoin.Miter))
}

fun DrawScope.drawStarFill(cx: Float, cy: Float, size: Float, color: Color, inner: Float = 0.78f) {
    drawPath(starPath(cx, cy, size, inner), color, style = Fill)
}

fun Modifier.starOrnaments(color: Color, vararg stars: StarSpec): Modifier = this.drawBehind {
    stars.forEach {
        drawStarOutline(it.x.toPx(), it.y.toPx(), it.size.toPx(), color.copy(alpha = it.alpha), 2.dp.toPx())
    }
}

@Composable
fun JStarBadge(
    label: String,
    modifier: Modifier = Modifier,
    size: Dp = 44.dp,
    fill: Color = Jawhar.colors.primaryContainer,
    textColor: Color = Jawhar.colors.onPrimaryContainer,
) {
    Box(modifier.size(size), contentAlignment = Alignment.Center) {
        Canvas(Modifier.size(size)) { drawStarFill(this.size.width / 2f, this.size.height / 2f, this.size.minDimension, fill) }
        JText(label, Jawhar.type.labelL, textColor)
    }
}

@Composable
fun JLogoMark(modifier: Modifier = Modifier, size: Dp = 88.dp, background: Color = Jawhar.colors.primary) {
    val c = Jawhar.colors
    val style = Jawhar.type.arabicHeading.copy(fontSize = (size.value * 0.36f).sp, lineHeight = (size.value * 0.5f).sp)
    Box(
        modifier
            .size(size)
            .clip(SquircleShape(size * 0.3f))
            .background(background)
            .drawBehind {
                val cx = this.size.width / 2f
                val cy = this.size.height / 2f
                drawStarOutline(cx, cy, this.size.minDimension * 0.82f, c.accent, (size.value * 0.018f).coerceAtLeast(1.5f).dp.toPx())
                drawStarFill(cx, cy, this.size.minDimension * 0.56f, c.accent, 0.72f)
            },
        contentAlignment = Alignment.Center,
    ) {
        JArabic("ج", style, c.onAccent)
    }
}
