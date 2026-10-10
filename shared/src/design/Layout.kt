package com.meher.jawhar.design

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxScope
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp

enum class JTab(val label: String, val icon: JI) {
    Home("Home", JI.Home),
    Learn("Learn", JI.Learn),
    Quran("Quran", JI.Quran),
    Tutor("Tutor", JI.Tutor),
    Profile("Profile", JI.User),
}

@Composable
fun JFloatingNav(selected: JTab, onSelect: (JTab) -> Unit, modifier: Modifier = Modifier) {
    val c = Jawhar.colors
    Row(
        modifier
            .fillMaxWidth()
            .height(68.dp)
            .softShadow(CapsuleShape, 16.dp, 0.3f)
            .clip(CapsuleShape)
            .background(c.bgSurface.copy(alpha = 0.94f))
            .padding(horizontal = 8.dp, vertical = 6.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        JTab.values().forEach { tab ->
            val on = tab == selected
            val tint = if (on) c.onPrimaryContainer else c.onSurfaceVariant
            Column(
                Modifier
                    .weight(1f)
                    .height(56.dp)
                    .clip(CapsuleShape)
                    .background(if (on) c.primaryContainer else Color.Transparent)
                    .tappable { onSelect(tab) },
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(3.dp, Alignment.CenterVertically),
            ) {
                JIcon(tab.icon, size = 22.dp, tint = tint)
                JText(tab.label, Jawhar.type.labelM, tint)
            }
        }
    }
}

@Composable
fun JScrim(onClick: () -> Unit = {}) {
    Box(Modifier.fillMaxSize().background(Jawhar.colors.scrim).tappable(onClick = onClick))
}

@Composable
fun JDialog(
    title: String,
    body: String,
    confirm: String,
    onConfirm: () -> Unit,
    onDismiss: () -> Unit,
    modifier: Modifier = Modifier,
    cancel: String? = "Cancel",
    icon: JI = JI.Logout,
    destructive: Boolean = false,
) {
    val c = Jawhar.colors
    Box(modifier.fillMaxSize()) {
        JScrim(onDismiss)
        Column(
            Modifier
                .align(Alignment.Center)
                .width(312.dp)
                .softShadow(SquircleShape(34.dp), 24.dp, 0.4f)
                .clip(SquircleShape(34.dp))
                .background(c.bgSurface)
                .padding(24.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            Box(
                Modifier.size(48.dp).clip(CircleShape).background(if (destructive) c.errorContainer else c.primaryContainer),
                contentAlignment = Alignment.Center,
            ) {
                JIcon(icon, size = 24.dp, tint = if (destructive) c.error else c.onPrimaryContainer)
            }
            JText(title, Jawhar.type.headlineS, c.onSurface)
            JText(body, Jawhar.type.bodyM, c.onSurfaceVariant)
            Row(Modifier.fillMaxWidth().padding(top = 8.dp), horizontalArrangement = Arrangement.End, verticalAlignment = Alignment.CenterVertically) {
                if (cancel != null) {
                    JText(cancel, Jawhar.type.labelL, c.primary, Modifier.tappable(onClick = onDismiss))
                    Spacer(Modifier.width(28.dp))
                }
                JText(confirm, Jawhar.type.labelL, if (destructive) c.error else c.primary, Modifier.tappable(onClick = onConfirm))
            }
        }
    }
}

@Composable
fun JBottomSheet(
    onDismiss: () -> Unit,
    modifier: Modifier = Modifier,
    content: @Composable ColumnScope.() -> Unit,
) {
    val c = Jawhar.colors
    Box(modifier.fillMaxSize()) {
        JScrim(onDismiss)
        Column(
            Modifier
                .align(Alignment.BottomCenter)
                .fillMaxWidth()
                .softShadow(SquircleTop(48.dp), 24.dp, 0.4f)
                .clip(SquircleTop(48.dp))
                .background(c.bgSurface)
                .padding(start = 24.dp, end = 24.dp, top = 10.dp, bottom = 24.dp + LocalBottomInset.current),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            Box(Modifier.size(40.dp, 5.dp).clip(CapsuleShape).background(c.outline))
            content()
        }
    }
}

@Composable
fun JScreen(
    modifier: Modifier = Modifier,
    background: Color = Jawhar.colors.bgBase,
    onBack: (() -> Unit)? = null,
    backIcon: JI = JI.Back,
    rightIcon: JI? = null,
    onRight: () -> Unit = {},
    title: String? = null,
    tab: JTab? = null,
    onTab: (JTab) -> Unit = {},
    cta: (@Composable () -> Unit)? = null,
    scroll: Boolean = true,
    spacing: Dp = 16.dp,
    topSpace: Dp = 68.dp,
    horizontalPadding: Dp = 24.dp,
    overlay: (@Composable BoxScope.() -> Unit)? = null,
    content: @Composable ColumnScope.() -> Unit,
) {
    val top = LocalTopInset.current
    val extraBottom = (LocalBottomInset.current - 24.dp).coerceAtLeast(0.dp)
    val hasBottom = tab != null || cta != null
    Box(modifier.fillMaxSize().background(background)) {
        val base = Modifier.fillMaxSize()
        Column(
            (if (scroll) base.verticalScroll(rememberScrollState()) else base).padding(horizontal = horizontalPadding),
            verticalArrangement = Arrangement.spacedBy(spacing),
        ) {
            Spacer(Modifier.height((top + topSpace - spacing).coerceAtLeast(0.dp)))
            content()
            Spacer(Modifier.height(if (hasBottom) 120.dp else 32.dp))
        }
        if (hasBottom) {
            Box(
                Modifier
                    .align(Alignment.BottomCenter)
                    .fillMaxWidth()
                    .height(150.dp)
                    .background(Brush.verticalGradient(0f to Color.Transparent, 0.5f to background, 1f to background)),
            )
        }
        if (tab != null) {
            Box(Modifier.align(Alignment.BottomCenter).padding(start = 24.dp, end = 24.dp, bottom = 22.dp + extraBottom)) {
                JFloatingNav(tab, onTab)
            }
        }
        if (cta != null) {
            Box(Modifier.align(Alignment.BottomCenter).padding(start = 24.dp, end = 24.dp, bottom = 22.dp + extraBottom)) {
                cta()
            }
        }
        Box(Modifier.fillMaxWidth().padding(top = top + 8.dp, start = 16.dp, end = 16.dp)) {
            if (onBack != null) JFloatingButton(backIcon, onBack, Modifier.align(Alignment.CenterStart))
            if (title != null) JGlassPill(title, Modifier.align(Alignment.Center))
            if (rightIcon != null) JFloatingButton(rightIcon, onRight, Modifier.align(Alignment.CenterEnd))
        }
        if (overlay != null) overlay()
    }
}
