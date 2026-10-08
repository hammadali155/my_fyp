package com.meher.jawhar.design

import androidx.compose.animation.core.animateDpAsState
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsPressedAsState
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.Slider
import androidx.compose.material3.SliderDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.focus.onFocusChanged
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp

enum class JButtonStyle { Filled, Tonal, Neutral, Text, Accent }

@Composable
fun JButton(
    text: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier.fillMaxWidth(),
    style: JButtonStyle = JButtonStyle.Filled,
    enabled: Boolean = true,
    icon: JI? = null,
    height: Dp = 52.dp,
) {
    val c = Jawhar.colors
    val source = remember { MutableInteractionSource() }
    val pressed by source.collectIsPressedAsState()
    val colors: Pair<Color, Color> = when (style) {
        JButtonStyle.Filled -> Pair(if (pressed) c.onPrimaryContainer else c.primary, c.onPrimary)
        JButtonStyle.Tonal -> Pair(if (pressed) c.outlineVariant else c.primaryContainer, c.onPrimaryContainer)
        JButtonStyle.Neutral -> Pair(if (pressed) c.bgSurfaceHigh else c.bgSurfaceVariant, c.onSurface)
        JButtonStyle.Text -> Pair(if (pressed) c.primarySoft else Color.Transparent, c.primary)
        JButtonStyle.Accent -> Pair(if (pressed) c.accentContainer else c.accent, if (pressed) c.onAccentContainer else c.onAccent)
    }
    val bg = colors.first
    val fg = colors.second
    val finalBg = if (enabled) bg else if (style == JButtonStyle.Text) Color.Transparent else c.onSurface.copy(alpha = 0.12f)
    val finalFg = if (enabled) fg else c.onSurface.copy(alpha = 0.38f)
    Box(
        modifier
            .height(height)
            .clip(CapsuleShape)
            .background(finalBg)
            .clickable(interactionSource = source, indication = null, enabled = enabled, onClick = onClick)
            .padding(horizontal = 24.dp),
        contentAlignment = Alignment.Center,
    ) {
        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            if (icon != null) JIcon(icon, size = 20.dp, tint = finalFg)
            JText(text, Jawhar.type.labelL, finalFg, textAlign = TextAlign.Center)
        }
    }
}

@Composable
fun JFloatingButton(
    icon: JI,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    filled: Boolean = false,
    size: Dp = 48.dp,
) {
    val c = Jawhar.colors
    Box(
        modifier
            .size(size)
            .softShadow(CircleShape, 14.dp, 0.3f)
            .clip(CircleShape)
            .background(if (filled) c.primary else c.bgSurface.copy(alpha = 0.92f))
            .tappable(onClick = onClick),
        contentAlignment = Alignment.Center,
    ) {
        JIcon(icon, size = 22.dp, tint = if (filled) c.onPrimary else c.onSurface)
    }
}

@Composable
fun JGlassPill(text: String, modifier: Modifier = Modifier) {
    val c = Jawhar.colors
    Box(
        modifier
            .height(44.dp)
            .softShadow(CapsuleShape, 14.dp, 0.3f)
            .clip(CapsuleShape)
            .background(c.bgSurface.copy(alpha = 0.92f))
            .padding(horizontal = 22.dp),
        contentAlignment = Alignment.Center,
    ) {
        JText(text, Jawhar.type.titleS, c.onSurface)
    }
}

@Composable
fun JTextField(
    value: String,
    onValueChange: (String) -> Unit,
    label: String,
    modifier: Modifier = Modifier.fillMaxWidth(),
    placeholder: String = "",
    helper: String? = null,
    isError: Boolean = false,
    enabled: Boolean = true,
    password: Boolean = false,
    trailing: JI? = null,
    keyboardType: KeyboardType = KeyboardType.Text,
) {
    val c = Jawhar.colors
    val t = Jawhar.type
    var focused by remember { mutableStateOf(false) }
    var reveal by remember { mutableStateOf(false) }
    val shape = SquircleShape(22.dp)
    Column(modifier, verticalArrangement = Arrangement.spacedBy(6.dp)) {
        JText(label, t.labelM, if (isError) c.error else if (focused) c.primary else c.onSurfaceVariant)
        Box(
            Modifier
                .fillMaxWidth()
                .height(56.dp)
                .clip(shape)
                .background(if (isError) c.errorContainer else c.bgSurfaceVariant)
                .then(if (focused) Modifier.border(2.dp, c.primary, shape) else Modifier)
                .padding(horizontal = 16.dp),
            contentAlignment = Alignment.CenterStart,
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                BasicTextField(
                    value = value,
                    onValueChange = onValueChange,
                    enabled = enabled,
                    singleLine = true,
                    textStyle = t.bodyL.copy(color = c.onSurface),
                    cursorBrush = SolidColor(c.primary),
                    visualTransformation = if (password && !reveal) PasswordVisualTransformation() else VisualTransformation.None,
                    keyboardOptions = KeyboardOptions(keyboardType = if (password) KeyboardType.Password else keyboardType),
                    modifier = Modifier.weight(1f).onFocusChanged { focused = it.isFocused },
                    decorationBox = { inner ->
                        Box(contentAlignment = Alignment.CenterStart) {
                            if (value.isEmpty()) JText(placeholder, t.bodyL, c.onSurfaceSubtle)
                            inner()
                        }
                    },
                )
                if (password) {
                    JIcon(
                        if (reveal) JI.EyeOff else JI.Eye,
                        Modifier.tappable { reveal = !reveal },
                        size = 20.dp,
                        tint = c.onSurfaceVariant,
                    )
                } else if (isError) {
                    JIcon(JI.Alert, size = 20.dp, tint = c.error)
                } else if (trailing != null) {
                    JIcon(trailing, size = 20.dp, tint = c.onSurfaceVariant)
                }
            }
        }
        if (helper != null) JText(helper, t.bodyS, if (isError) c.error else c.onSurfaceVariant)
    }
}

@Composable
fun JChip(label: String, selected: Boolean, onClick: () -> Unit, modifier: Modifier = Modifier) {
    val c = Jawhar.colors
    Row(
        modifier
            .height(36.dp)
            .clip(CapsuleShape)
            .background(if (selected) c.primaryContainer else c.bgSurfaceVariant)
            .tappable(onClick = onClick)
            .padding(horizontal = 16.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(6.dp),
    ) {
        if (selected) JIcon(JI.Check, size = 16.dp, tint = c.onPrimaryContainer, strokeWidth = 2.dp)
        JText(label, Jawhar.type.labelL, if (selected) c.onPrimaryContainer else c.onSurfaceVariant)
    }
}

@Composable
fun JSwitch(checked: Boolean, onCheckedChange: (Boolean) -> Unit, modifier: Modifier = Modifier) {
    val c = Jawhar.colors
    val thumbX by animateDpAsState(if (checked) 24.dp else 4.dp)
    Box(
        modifier
            .size(52.dp, 32.dp)
            .clip(CapsuleShape)
            .background(if (checked) c.primary else c.bgSurfaceHigh)
            .tappable { onCheckedChange(!checked) },
    ) {
        val thumb = if (checked) 24.dp else 16.dp
        Box(
            Modifier
                .offset(x = if (checked) thumbX else thumbX + 4.dp, y = (32.dp - thumb) / 2)
                .size(thumb)
                .clip(CircleShape)
                .background(if (checked) c.onPrimary else c.outline),
        )
    }
}

@Composable
fun JSearchField(
    value: String,
    onValueChange: (String) -> Unit,
    placeholder: String,
    modifier: Modifier = Modifier.fillMaxWidth(),
) {
    val c = Jawhar.colors
    val t = Jawhar.type
    var focused by remember { mutableStateOf(false) }
    Row(
        modifier
            .height(52.dp)
            .clip(CapsuleShape)
            .background(c.bgSurfaceVariant)
            .then(if (focused) Modifier.border(2.dp, c.primary, CapsuleShape) else Modifier)
            .padding(horizontal = 16.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        JIcon(JI.Search, size = 22.dp, tint = c.onSurfaceVariant)
        BasicTextField(
            value = value,
            onValueChange = onValueChange,
            singleLine = true,
            textStyle = t.bodyL.copy(color = c.onSurface),
            cursorBrush = SolidColor(c.primary),
            modifier = Modifier.weight(1f).onFocusChanged { focused = it.isFocused },
            decorationBox = { inner ->
                Box(contentAlignment = Alignment.CenterStart) {
                    if (value.isEmpty()) JText(placeholder, t.bodyL, c.onSurfaceSubtle)
                    inner()
                }
            },
        )
        JIcon(JI.Mic, size = 22.dp, tint = c.onSurfaceVariant)
    }
}

@Composable
fun JSegmented(options: List<String>, selected: Int, onSelect: (Int) -> Unit, modifier: Modifier = Modifier.fillMaxWidth()) {
    val c = Jawhar.colors
    Row(
        modifier
            .height(44.dp)
            .clip(CapsuleShape)
            .background(c.bgSurfaceVariant)
            .padding(4.dp),
    ) {
        options.forEachIndexed { i, label ->
            Box(
                Modifier
                    .weight(1f)
                    .height(36.dp)
                    .clip(CapsuleShape)
                    .background(if (i == selected) c.bgSurface else Color.Transparent)
                    .tappable { onSelect(i) },
                contentAlignment = Alignment.Center,
            ) {
                JText(label, Jawhar.type.labelL, if (i == selected) c.onSurface else c.onSurfaceVariant)
            }
        }
    }
}

@Composable
fun JSlider(value: Float, onValueChange: (Float) -> Unit, modifier: Modifier = Modifier.fillMaxWidth()) {
    val c = Jawhar.colors
    Slider(
        value = value,
        onValueChange = onValueChange,
        modifier = modifier,
        colors = SliderDefaults.colors(
            thumbColor = c.primary,
            activeTrackColor = c.primary,
            inactiveTrackColor = c.bgSurfaceHigh,
        ),
    )
}
