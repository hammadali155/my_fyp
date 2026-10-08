package com.meher.jawhar.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxScope
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.meher.jawhar.design.*
import com.meher.jawhar.nav.LocalNav

@Composable
fun Page(
    title: String? = null,
    right: JI? = null,
    onRight: () -> Unit = {},
    back: Boolean = true,
    backIcon: JI = JI.Back,
    tab: JTab? = null,
    cta: (@Composable () -> Unit)? = null,
    scroll: Boolean = true,
    spacing: Dp = 16.dp,
    background: Color = Jawhar.colors.bgBase,
    overlay: (@Composable BoxScope.() -> Unit)? = null,
    content: @Composable ColumnScope.() -> Unit,
) {
    val nav = LocalNav.current
    JScreen(
        background = background,
        onBack = if (back && tab == null) ({ nav.back() }) else null,
        backIcon = backIcon,
        rightIcon = right,
        onRight = onRight,
        title = title,
        tab = tab,
        onTab = { nav.tab(it) },
        cta = cta,
        scroll = scroll,
        spacing = spacing,
        overlay = overlay,
        content = content,
    )
}

@Composable
fun BigTitle(text: String, sub: String? = null, modifier: Modifier = Modifier.fillMaxWidth(), center: Boolean = false) {
    val align = if (center) TextAlign.Center else TextAlign.Start
    Column(modifier, verticalArrangement = Arrangement.spacedBy(8.dp)) {
        JText(text, Jawhar.type.headlineL, Jawhar.colors.onSurface, Modifier.fillMaxWidth(), align)
        if (sub != null) JText(sub, Jawhar.type.bodyL, Jawhar.colors.onSurfaceVariant, Modifier.fillMaxWidth(), align)
    }
}

@Composable
fun SectionTitle(text: String, action: String? = null, onAction: () -> Unit = {}) {
    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
        JText(text, Jawhar.type.titleL, Jawhar.colors.onSurface)
        if (action != null) JText(action, Jawhar.type.labelL, Jawhar.colors.primary, Modifier.tappable(onClick = onAction))
    }
}

@Composable
fun HeroCard(
    modifier: Modifier = Modifier.fillMaxWidth(),
    color: Color = Jawhar.colors.primary,
    starColor: Color = Jawhar.colors.accent,
    stars: List<StarSpec> = listOf(StarSpec(330.dp, 20.dp, 240.dp, 0.26f)),
    radius: Dp = 34.dp,
    padding: Dp = 24.dp,
    content: @Composable ColumnScope.() -> Unit,
) {
    Column(
        modifier
            .clip(SquircleShape(radius))
            .background(color)
            .starOrnaments(starColor, *stars.toTypedArray())
            .padding(padding),
        content = content,
    )
}

@Composable
fun StatefulField(
    label: String,
    initial: String = "",
    placeholder: String = "",
    helper: String? = null,
    isError: Boolean = false,
    password: Boolean = false,
    trailing: JI? = null,
    keyboardType: KeyboardType = KeyboardType.Text,
) {
    var value by remember { mutableStateOf(initial) }
    JTextField(value, { value = it }, label, placeholder = placeholder, helper = helper, isError = isError, password = password, trailing = trailing, keyboardType = keyboardType)
}

@Composable
fun CircleIcon(icon: JI, tile: Color, tint: Color, size: Dp = 104.dp, iconSize: Dp = 44.dp) {
    Box(Modifier.size(size).clip(CircleShape).background(tile), contentAlignment = Alignment.Center) {
        JIcon(icon, size = iconSize, tint = tint, strokeWidth = 1.6.dp)
    }
}

@Composable
fun TwoButtons(left: String, onLeft: () -> Unit, right: String, onRight: () -> Unit, leftStyle: JButtonStyle = JButtonStyle.Tonal) {
    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        JButton(left, onLeft, Modifier.weight(1f), style = leftStyle)
        JButton(right, onRight, Modifier.weight(1f))
    }
}

@Composable
fun OrDivider() {
    Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
        Box(Modifier.weight(1f).size(1.dp).background(Jawhar.colors.outlineVariant))
        JText("or", Jawhar.type.labelM, Jawhar.colors.onSurfaceSubtle)
        Box(Modifier.weight(1f).size(1.dp).background(Jawhar.colors.outlineVariant))
    }
}

@Composable
fun FooterLink(prefix: String, link: String, onClick: () -> Unit) {
    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.Center, verticalAlignment = Alignment.CenterVertically) {
        JText(prefix, Jawhar.type.bodyM, Jawhar.colors.onSurfaceVariant)
        JText(" $link", Jawhar.type.labelL, Jawhar.colors.primary, Modifier.tappable(onClick = onClick))
    }
}

@Composable
fun PageDots(count: Int, active: Int, modifier: Modifier = Modifier) {
    Row(modifier, horizontalArrangement = Arrangement.spacedBy(6.dp), verticalAlignment = Alignment.CenterVertically) {
        repeat(count) { i ->
            Box(
                Modifier
                    .size(width = if (i == active) 28.dp else 8.dp, height = 8.dp)
                    .clip(CapsuleShape)
                    .background(if (i == active) Jawhar.colors.primary else Jawhar.colors.outline),
            )
        }
    }
}

@Composable
fun BoxScope.TopProgress(progress: Float, label: String) {
    val top = LocalTopInset.current
    Row(
        Modifier.align(Alignment.TopStart).fillMaxWidth().padding(top = top + 8.dp, start = 76.dp, end = 24.dp).height(48.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        JProgressBar(progress, Modifier.weight(1f))
        JText(label, Jawhar.type.labelL, Jawhar.colors.onSurfaceVariant)
    }
}

@Composable
fun CheckRow(checked: Boolean, onChange: (Boolean) -> Unit, label: String, error: String? = null) {
    val c = Jawhar.colors
    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            Box(
                Modifier.size(24.dp).clip(SquircleShape(8.dp)).background(if (checked) c.primary else c.bgSurfaceHigh).tappable { onChange(!checked) },
                contentAlignment = Alignment.Center,
            ) {
                if (checked) JIcon(JI.Check, size = 16.dp, tint = c.onPrimary, strokeWidth = 2.4.dp)
            }
            JText(label, Jawhar.type.bodyM, c.onSurfaceVariant)
        }
        if (error != null) JText(error, Jawhar.type.bodyS, c.error, Modifier.padding(start = 34.dp))
    }
}

@Composable
fun StateScreen(
    icon: JI,
    tile: Color,
    tint: Color,
    title: String,
    body: String,
    primary: String,
    secondary: String? = null,
    onPrimary: () -> Unit = {},
    onSecondary: () -> Unit = {},
    back: Boolean = false,
) {
    Page(
        back = back,
        scroll = false,
        cta = {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                JButton(primary, onPrimary)
                if (secondary != null) JButton(secondary, onSecondary, style = JButtonStyle.Text)
            }
        },
    ) {
        Box(Modifier.fillMaxWidth().padding(top = 70.dp), contentAlignment = Alignment.Center) {
            JCenterState(icon, tile, tint, title, body)
        }
    }
}
