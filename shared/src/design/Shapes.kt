package com.meher.jawhar.design

import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.RoundRect
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Outline
import androidx.compose.ui.graphics.Shape
import androidx.compose.ui.graphics.vector.PathParser
import androidx.compose.ui.unit.Density
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.unit.dp
import kotlin.math.PI
import kotlin.math.cos
import kotlin.math.min
import kotlin.math.roundToInt
import kotlin.math.sin
import kotlin.math.sqrt
import kotlin.math.tan

val CapsuleShape = RoundedCornerShape(percent = 50)

class SquircleShape(
    private val topStart: Dp,
    private val topEnd: Dp,
    private val bottomEnd: Dp,
    private val bottomStart: Dp,
    private val smoothing: Float = 0.6f,
) : Shape {
    constructor(radius: Dp, smoothing: Float = 0.6f) : this(radius, radius, radius, radius, smoothing)

    override fun createOutline(size: Size, layoutDirection: LayoutDirection, density: Density): Outline {
        val w = size.width
        val h = size.height
        val budget = min(w, h) / 2f
        val radii = with(density) {
            listOf(topStart.toPx(), topEnd.toPx(), bottomEnd.toPx(), bottomStart.toPx())
        }
        if (radii.all { it >= budget - 0.5f }) {
            return Outline.Rounded(RoundRect(0f, 0f, w, h, CornerRadius(budget, budget)))
        }
        val d = squircleSvg(w, h, radii.map { min(it, budget) }, smoothing)
        return Outline.Generic(PathParser().parsePathString(d).toPath())
    }
}

fun Squircle(radius: Dp) = SquircleShape(radius)

fun SquircleTop(radius: Dp) = SquircleShape(radius, radius, 0.dp, 0.dp)

private class Corner(val a: Float, val b: Float, val c: Float, val d: Float, val p: Float, val arc: Float, val r: Float)

private fun rad(deg: Float) = (deg * PI / 180.0).toFloat()

private fun num(v: Float): String {
    val r = (v * 1000f).roundToInt()
    val neg = r < 0
    val a = if (neg) -r else r
    val frac = (a % 1000).toString().padStart(3, '0')
    return (if (neg) "-" else "") + (a / 1000).toString() + "." + frac
}

private fun corner(r: Float, sm: Float, budget: Float): Corner? {
    if (r <= 0f) return null
    var p = (1f + sm) * r
    p = min(p, budget)
    val s2 = min(sm, budget / r - 1f)
    val arcMeasure = 90f * (1f - s2)
    val arc = sin(rad(arcMeasure / 2f)) * r * sqrt(2f)
    val alpha = (90f - arcMeasure) / 2f
    val p34 = r * tan(rad(alpha / 2f))
    val beta = 45f * s2
    val c = p34 * cos(rad(beta))
    val d = c * tan(rad(beta))
    val b = (p - arc - c - d) / 3f
    val a = 2f * b
    return Corner(a, b, c, d, p, arc, r)
}

private fun squircleSvg(w: Float, h: Float, rs: List<Float>, sm: Float): String {
    val budget = min(w, h) / 2f
    val tl = corner(rs[0], sm, budget)
    val tr = corner(rs[1], sm, budget)
    val br = corner(rs[2], sm, budget)
    val bl = corner(rs[3], sm, budget)
    val sb = StringBuilder()
    sb.append("M").append(num(w - (tr?.p ?: 0f))).append(" 0")
    if (tr != null) {
        with(tr) {
            sb.append("c").append(num(a)).append(" 0 ").append(num(a + b)).append(" 0 ").append(num(a + b + c)).append(" ").append(num(d))
            sb.append("a").append(num(r)).append(" ").append(num(r)).append(" 0 0 1 ").append(num(arc)).append(" ").append(num(arc))
            sb.append("c").append(num(d)).append(" ").append(num(c)).append(" ").append(num(d)).append(" ").append(num(b + c)).append(" ").append(num(d)).append(" ").append(num(a + b + c))
        }
    }
    sb.append("L").append(num(w)).append(" ").append(num(h - (br?.p ?: 0f)))
    if (br != null) {
        with(br) {
            sb.append("c0 ").append(num(a)).append(" 0 ").append(num(a + b)).append(" ").append(num(-d)).append(" ").append(num(a + b + c))
            sb.append("a").append(num(r)).append(" ").append(num(r)).append(" 0 0 1 ").append(num(-arc)).append(" ").append(num(arc))
            sb.append("c").append(num(-c)).append(" ").append(num(d)).append(" ").append(num(-(b + c))).append(" ").append(num(d)).append(" ").append(num(-(a + b + c))).append(" ").append(num(d))
        }
    }
    sb.append("L").append(num(bl?.p ?: 0f)).append(" ").append(num(h))
    if (bl != null) {
        with(bl) {
            sb.append("c").append(num(-a)).append(" 0 ").append(num(-(a + b))).append(" 0 ").append(num(-(a + b + c))).append(" ").append(num(-d))
            sb.append("a").append(num(r)).append(" ").append(num(r)).append(" 0 0 1 ").append(num(-arc)).append(" ").append(num(-arc))
            sb.append("c").append(num(-d)).append(" ").append(num(-c)).append(" ").append(num(-d)).append(" ").append(num(-(b + c))).append(" ").append(num(-d)).append(" ").append(num(-(a + b + c)))
        }
    }
    sb.append("L0 ").append(num(tl?.p ?: 0f))
    if (tl != null) {
        with(tl) {
            sb.append("c0 ").append(num(-a)).append(" 0 ").append(num(-(a + b))).append(" ").append(num(d)).append(" ").append(num(-(a + b + c)))
            sb.append("a").append(num(r)).append(" ").append(num(r)).append(" 0 0 1 ").append(num(arc)).append(" ").append(num(-arc))
            sb.append("c").append(num(c)).append(" ").append(num(-d)).append(" ").append(num(b + c)).append(" ").append(num(-d)).append(" ").append(num(a + b + c)).append(" ").append(num(-d))
        }
    }
    sb.append("Z")
    return sb.toString()
}
