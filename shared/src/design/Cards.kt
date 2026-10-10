package com.meher.jawhar.design

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxScope
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.RowScope
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Shape
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp

@Composable
fun JCard(
    modifier: Modifier = Modifier,
    color: Color = Jawhar.colors.bgSurfaceVariant,
    radius: Dp = 28.dp,
    padding: Dp = 16.dp,
    content: @Composable ColumnScope.() -> Unit,
) {
    Column(
        modifier
            .clip(SquircleShape(radius))
            .background(color)
            .padding(padding),
        content = content,
    )
}

@Composable
fun JTag(
    text: String,
    modifier: Modifier = Modifier,
    background: Color = Jawhar.colors.bgSurface,
    color: Color = Jawhar.colors.onSurface,
    icon: JI? = null,
    height: Dp = 32.dp,
) {
    Row(
        modifier
            .height(height)
            .clip(CapsuleShape)
            .background(background)
            .padding(horizontal = 14.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(6.dp),
    ) {
        if (icon != null) JIcon(icon, size = 16.dp, tint = color)
        JText(text, Jawhar.type.labelM, color)
    }
}

@Composable
fun JSectionLabel(text: String, modifier: Modifier = Modifier) {
    JText(text.uppercase(), Jawhar.type.labelS, Jawhar.colors.onSurfaceSubtle, modifier.padding(horizontal = 4.dp))
}

@Composable
fun JListItem(
    title: String,
    modifier: Modifier = Modifier.fillMaxWidth(),
    subtitle: String? = null,
    icon: JI? = null,
    tile: Color = Jawhar.colors.primaryContainer,
    tileTint: Color = Jawhar.colors.onPrimaryContainer,
    onClick: (() -> Unit)? = null,
    trailing: (@Composable RowScope.() -> Unit)? = { JIcon(JI.Chevron, size = 20.dp, tint = Jawhar.colors.onSurfaceSubtle) },
) {
    val c = Jawhar.colors
    val t = Jawhar.type
    val base = modifier
        .clip(SquircleShape(26.dp))
        .background(c.bgSurfaceVariant)
    Row(
        (if (onClick != null) base.tappable(onClick = onClick) else base).padding(horizontal = 16.dp, vertical = 12.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        if (icon != null) {
            Box(Modifier.size(40.dp).clip(SquircleShape(12.dp)).background(tile), contentAlignment = Alignment.Center) {
                JIcon(icon, size = 20.dp, tint = tileTint)
            }
        }
        Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
            JText(title, t.titleM, c.onSurface)
            if (subtitle != null) JText(subtitle, t.bodyS, c.onSurfaceVariant)
        }
        if (trailing != null) trailing()
    }
}

enum class JQuizState { Default, Selected, Correct, Incorrect }

@Composable
fun JQuizOption(
    text: String,
    letter: String,
    state: JQuizState,
    onClick: () -> Unit,
    modifier: Modifier = Modifier.fillMaxWidth(),
    arabic: Boolean = false,
) {
    val c = Jawhar.colors
    val t = Jawhar.type
    val fill = when (state) {
        JQuizState.Default -> c.bgSurfaceVariant
        JQuizState.Selected -> c.primaryContainer
        JQuizState.Correct -> c.successContainer
        JQuizState.Incorrect -> c.errorContainer
    }
    val accent = when (state) {
        JQuizState.Default -> c.outline
        JQuizState.Selected -> c.primary
        JQuizState.Correct -> c.success
        JQuizState.Incorrect -> c.error
    }
    Row(
        modifier
            .height(60.dp)
            .clip(SquircleShape(24.dp))
            .background(fill)
            .tappable(onClick = onClick)
            .padding(horizontal = 16.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Box(Modifier.size(30.dp), contentAlignment = Alignment.Center) {
            Canvas(Modifier.size(30.dp)) {
                drawCircle(accent, radius = this.size.minDimension / 2f - 0.75.dp.toPx(), style = Stroke(width = 1.5.dp.toPx()))
            }
            JText(letter, t.labelL, if (state == JQuizState.Default) c.onSurfaceVariant else accent)
        }
        Box(Modifier.weight(1f)) {
            if (arabic) JArabic(text, t.arabicTitle, c.onSurface, Modifier.fillMaxWidth(), TextAlign.End)
            else JText(text, t.bodyL, c.onSurface)
        }
        if (state == JQuizState.Correct) JIcon(JI.Check, size = 22.dp, tint = c.success)
        if (state == JQuizState.Incorrect) JIcon(JI.Close, size = 22.dp, tint = c.error)
    }
}

enum class GrammarRole(val label: String) {
    Faail("FA'IL"), Maful("MAF'UL BIHI"), Mubtada("MUBTADA"), Khabar("KHABAR"),
    Nat("NA'T"), Harf("HARF"), Mudaf("MUDAF ILAYH");

    fun color(c: JawharColors): Color = when (this) {
        Faail -> c.roleFaail
        Maful -> c.roleMaful
        Mubtada -> c.roleMubtada
        Khabar -> c.roleKhabar
        Nat -> c.roleNat
        Harf -> c.roleHarf
        Mudaf -> c.roleMudaf
    }
}

@Composable
fun JWordChip(
    word: String,
    role: GrammarRole,
    modifier: Modifier = Modifier,
    selected: Boolean = false,
    onClick: (() -> Unit)? = null,
) {
    val c = Jawhar.colors
    val col = role.color(c)
    val base = modifier.clip(SquircleShape(20.dp)).background(col.copy(alpha = if (selected) 0.28f else 0.12f))
    Column(
        (if (onClick != null) base.tappable(onClick = onClick) else base).padding(horizontal = 14.dp, vertical = 8.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        JArabic(word, Jawhar.type.arabicQuranM, col)
        JText(role.label, Jawhar.type.labelS, col)
    }
}

enum class JBannerKind { Info, Success, Warning, Error, Offline }

@Composable
fun JBanner(kind: JBannerKind, title: String, message: String, modifier: Modifier = Modifier.fillMaxWidth(), floating: Boolean = false) {
    val c = Jawhar.colors
    val t = Jawhar.type
    val spec: Triple<JI, Color, Color> = when (kind) {
        JBannerKind.Info -> Triple(JI.Info, c.infoContainer, c.info)
        JBannerKind.Success -> Triple(JI.Check, c.successContainer, c.success)
        JBannerKind.Warning -> Triple(JI.Alert, c.accentContainer, c.onAccentContainer)
        JBannerKind.Error -> Triple(JI.Alert, c.errorContainer, c.error)
        JBannerKind.Offline -> Triple(JI.WifiOff, c.bgSurfaceHigh, c.onSurfaceVariant)
    }
    val shape = SquircleShape(24.dp)
    Row(
        (if (floating) modifier.softShadow(shape, 12.dp, 0.25f) else modifier)
            .clip(shape)
            .background(spec.second)
            .padding(14.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        JIcon(spec.first, size = 22.dp, tint = spec.third)
        Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
            JText(title, t.titleS, c.onSurface)
            JText(message, t.bodyS, c.onSurfaceVariant)
        }
    }
}

@Composable
fun JSnackbar(message: String, action: String, modifier: Modifier = Modifier.fillMaxWidth(), kind: JBannerKind? = null, onAction: () -> Unit = {}) {
    val c = Jawhar.colors
    val shape = SquircleShape(24.dp)
    Row(
        modifier
            .softShadow(shape, 12.dp, 0.3f)
            .clip(shape)
            .background(c.bgInverse)
            .padding(horizontal = 16.dp, vertical = 14.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        if (kind == JBannerKind.Success) JIcon(JI.Check, size = 20.dp, tint = c.success)
        if (kind == JBannerKind.Error) JIcon(JI.Alert, size = 20.dp, tint = c.error)
        JText(message, Jawhar.type.bodyM, c.onInverse, Modifier.weight(1f))
        JText(action, Jawhar.type.labelL, c.accent, Modifier.tappable(onClick = onAction))
    }
}

enum class JTone { Neutral, Primary, Accent, Info }

@Composable
fun JInfoCard(
    title: String,
    body: String,
    modifier: Modifier = Modifier.fillMaxWidth(),
    tone: JTone = JTone.Neutral,
    icon: JI = JI.Bulb,
) {
    val c = Jawhar.colors
    val spec: Triple<Color, Color, Color> = when (tone) {
        JTone.Neutral -> Triple(c.bgSurfaceVariant, c.onPrimaryContainer, c.primaryContainer)
        JTone.Primary -> Triple(c.primaryContainer, c.onPrimaryContainer, c.bgSurface)
        JTone.Accent -> Triple(c.accentContainer, c.onAccentContainer, c.bgSurface)
        JTone.Info -> Triple(c.infoContainer, c.info, c.bgSurface)
    }
    Column(
        modifier.clip(SquircleShape(28.dp)).background(spec.first).padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            Box(Modifier.size(36.dp).clip(CircleShape).background(spec.third), contentAlignment = Alignment.Center) {
                JIcon(icon, size = 20.dp, tint = spec.second)
            }
            JText(title, Jawhar.type.titleM, c.onSurface)
        }
        JText(body, Jawhar.type.bodyM, c.onSurfaceVariant)
    }
}

@Composable
fun JStatTile(icon: JI, value: String, label: String, fill: Color, tint: Color, modifier: Modifier = Modifier) {
    Column(
        modifier.clip(SquircleShape(26.dp)).background(fill).padding(14.dp),
        verticalArrangement = Arrangement.spacedBy(4.dp),
    ) {
        JIcon(icon, size = 22.dp, tint = tint)
        JText(value, Jawhar.type.headlineS, Jawhar.colors.onSurface)
        JText(label, Jawhar.type.labelM, Jawhar.colors.onSurfaceVariant)
    }
}

@Composable
fun JBadgeTile(title: String, caption: String, unlocked: Boolean, modifier: Modifier = Modifier) {
    val c = Jawhar.colors
    Column(modifier, horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(6.dp)) {
        Box(
            Modifier.size(72.dp).clip(CircleShape).background(if (unlocked) c.accentContainer else c.bgSurfaceVariant),
            contentAlignment = Alignment.Center,
        ) {
            JIcon(if (unlocked) JI.Trophy else JI.Lock, size = 30.dp, tint = if (unlocked) c.onAccentContainer else c.onSurfaceSubtle)
        }
        JText(title, Jawhar.type.labelM, c.onSurface, textAlign = TextAlign.Center)
        JText(caption, Jawhar.type.bodyS, c.onSurfaceVariant, textAlign = TextAlign.Center)
    }
}

@Composable
fun JProgressBar(progress: Float, modifier: Modifier = Modifier.fillMaxWidth(), height: Dp = 8.dp, track: Color = Jawhar.colors.outlineVariant, fill: Color = Jawhar.colors.primary) {
    Box(modifier.height(height).clip(CapsuleShape).background(track)) {
        Box(Modifier.fillMaxHeight().fillMaxWidth(progress.coerceIn(0f, 1f)).clip(CapsuleShape).background(fill))
    }
}

@Composable
fun JProgressRing(progress: Float, modifier: Modifier = Modifier, size: Dp = 168.dp, strokeWidth: Dp = 14.dp, content: @Composable BoxScope.() -> Unit = {}) {
    val c = Jawhar.colors
    Box(modifier.size(size), contentAlignment = Alignment.Center) {
        Canvas(Modifier.size(size)) {
            val sw = strokeWidth.toPx()
            val inset = sw / 2f
            val arcSize = Size(this.size.width - sw, this.size.height - sw)
            drawArc(c.outlineVariant, 0f, 360f, false, Offset(inset, inset), arcSize, style = Stroke(sw))
            drawArc(c.primary, -90f, 360f * progress, false, Offset(inset, inset), arcSize, style = Stroke(sw, cap = StrokeCap.Round))
        }
        content()
    }
}

enum class JNodeState { Completed, Current, Locked }

@Composable
fun JLessonNode(label: String, state: JNodeState, modifier: Modifier = Modifier, onClick: () -> Unit = {}) {
    val c = Jawhar.colors
    Column(modifier.tappable(onClick = onClick), horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(8.dp)) {
        val fill = when (state) {
            JNodeState.Completed -> c.primary
            JNodeState.Current -> c.accent
            JNodeState.Locked -> c.bgSurfaceHigh
        }
        Box(
            (if (state == JNodeState.Current) Modifier.softShadow(CircleShape, 12.dp, 0.3f) else Modifier)
                .size(72.dp)
                .clip(CircleShape)
                .background(fill),
            contentAlignment = Alignment.Center,
        ) {
            when (state) {
                JNodeState.Completed -> JIcon(JI.Check, size = 30.dp, tint = c.onPrimary, strokeWidth = 2.2.dp)
                JNodeState.Current -> JIcon(JI.Play, size = 30.dp, tint = c.onAccent, filled = true)
                JNodeState.Locked -> JIcon(JI.Lock, size = 30.dp, tint = c.onSurfaceSubtle)
            }
        }
        JText(label, Jawhar.type.labelM, if (state == JNodeState.Locked) c.onSurfaceSubtle else c.onSurface, textAlign = TextAlign.Center)
    }
}

enum class JRating(val label: String, val interval: String) {
    Again("Again", "<1m"), Hard("Hard", "1d"), Good("Good", "3d"), Easy("Easy", "7d")
}

@Composable
fun JRatingButton(rating: JRating, onClick: () -> Unit, modifier: Modifier = Modifier) {
    val c = Jawhar.colors
    val spec: Pair<Color, Color> = when (rating) {
        JRating.Again -> Pair(c.errorContainer, c.error)
        JRating.Hard -> Pair(c.accentContainer, c.onAccentContainer)
        JRating.Good -> Pair(c.primaryContainer, c.onPrimaryContainer)
        JRating.Easy -> Pair(c.infoContainer, c.info)
    }
    Column(
        modifier.height(64.dp).clip(SquircleShape(22.dp)).background(spec.first).tappable(onClick = onClick),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center,
    ) {
        JText(rating.label, Jawhar.type.titleS, spec.second)
        JText(rating.interval, Jawhar.type.bodyS, spec.second)
    }
}

@Composable
fun JAvatar(initials: String, modifier: Modifier = Modifier, size: Dp = 48.dp) {
    val c = Jawhar.colors
    Box(modifier.size(size).clip(CircleShape).background(c.accentContainer), contentAlignment = Alignment.Center) {
        JText(initials, if (size > 60.dp) Jawhar.type.titleL else if (size > 40.dp) Jawhar.type.labelL else Jawhar.type.labelM, c.onAccentContainer)
    }
}

@Composable
fun JChatBubble(text: String, fromUser: Boolean, modifier: Modifier = Modifier) {
    val c = Jawhar.colors
    val shape = if (fromUser) SquircleShape(24.dp, 24.dp, 6.dp, 24.dp) else SquircleShape(6.dp, 24.dp, 24.dp, 24.dp)
    Row(modifier.fillMaxWidth(), horizontalArrangement = if (fromUser) Arrangement.End else Arrangement.Start) {
        Box(
            Modifier
                .widthIn(max = 296.dp)
                .clip(shape)
                .background(if (fromUser) c.primary else c.bgSurfaceVariant)
                .padding(14.dp),
        ) {
            JText(text, Jawhar.type.bodyM, if (fromUser) c.onPrimary else c.onSurface)
        }
    }
}

@Composable
fun JSkeleton(modifier: Modifier = Modifier, radius: Dp = 12.dp, color: Color = Jawhar.colors.bgSurfaceHigh) {
    Box(modifier.clip(SquircleShape(radius)).background(color))
}

@Composable
fun JCenterState(
    icon: JI,
    tile: Color,
    tint: Color,
    title: String,
    body: String,
    modifier: Modifier = Modifier,
) {
    Column(modifier.fillMaxWidth().padding(horizontal = 40.dp), horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Box(Modifier.size(144.dp), contentAlignment = Alignment.Center) {
            Box(Modifier.size(144.dp).starOrnaments(Jawhar.colors.accent, StarSpec(72.dp, 72.dp, 140.dp, 0.3f)))
            Box(Modifier.size(104.dp).clip(CircleShape).background(tile), contentAlignment = Alignment.Center) {
                JIcon(icon, size = 52.dp, tint = tint, strokeWidth = 1.6.dp)
            }
        }
        JText(title, Jawhar.type.headlineM, Jawhar.colors.onSurface, textAlign = TextAlign.Center)
        JText(body, Jawhar.type.bodyL, Jawhar.colors.onSurfaceVariant, textAlign = TextAlign.Center)
    }
}
