package com.meher.jawhar

import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.Crossfade
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.slideInHorizontally
import androidx.compose.animation.slideOutHorizontally
import androidx.compose.animation.togetherWith
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.getValue
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.meher.jawhar.data.AppState
import com.meher.jawhar.data.LocalApi
import com.meher.jawhar.data.ThemeMode
import com.meher.jawhar.design.*
import com.meher.jawhar.nav.Dest
import com.meher.jawhar.nav.JNav
import com.meher.jawhar.nav.LocalNav
import com.meher.jawhar.nav.LocalSession
import com.meher.jawhar.nav.ScreenSession
import com.meher.jawhar.screens.GalleryPanel
import com.meher.jawhar.screens.ScreenSpec
import com.meher.jawhar.screens.Screens
import org.jetbrains.compose.reload.DevelopmentEntryPoint

import com.meher.jawhar.nav.SystemBackHandler

private val activeCatalog: Map<String, ScreenSpec>
    get() = if (AppState.galleryEnabled) Screens.byId else Screens.real

@Composable
@Preview
@DevelopmentEntryPoint
fun App() {
    val systemDark = isSystemInDarkTheme()
    val dark = when (AppState.themeMode) {
        ThemeMode.System -> systemDark
        ThemeMode.Light -> false
        ThemeMode.Dark -> true
    }
    JawharTheme(dark = dark) {
        val nav = remember { JNav(Dest.Splash) }
        val session = remember { ScreenSession() }
        val canHandleBack = nav.canGoBack || (nav.current in Dest.TabDestinations && nav.current != Dest.Home)

        // Resolve backend URL before composing any screen content to avoid
        // race condition where API calls hit localhost before fallback.
        val resolvedState = remember { mutableStateOf(false) }
        LaunchedEffect(Unit) {
            AppState.resolveBackendUrl()
            resolvedState.value = true
        }

        if (!resolvedState.value) {
            Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                JText("Connecting to backend…", Jawhar.type.bodyM, Jawhar.colors.onSurfaceVariant)
            }
        } else {
            SystemBackHandler(enabled = canHandleBack) {
                if (nav.canGoBack) {
                    nav.back()
                } else if (nav.current != Dest.Home) {
                    nav.tab(JTab.Home)
                }
            }

            if (AppState.isUsingLocalBackend) {
                LocalBackendIndicator()
            }

            CompositionLocalProvider(LocalNav provides nav, LocalSession provides session, LocalApi provides AppState.api) {
                BoxWithConstraints(Modifier.fillMaxSize().background(Jawhar.colors.bgBase)) {
                    if (maxWidth > 760.dp && maxHeight > 560.dp) {
                        DesktopShell(nav, maxHeight)
                    } else {
                        PhoneHost(nav)
                    }
                }
            }
        }
    }
}

@Composable
private fun ScreenHost(nav: JNav) {
    AnimatedContent(
        targetState = nav.current,
        label = "screen_stack",
        transitionSpec = {
            val isTab = nav.isTabSwitch || (initialState in Dest.TabDestinations && targetState in Dest.TabDestinations)
            if (isTab) {
                fadeIn(animationSpec = motion(JawharMotion.effectsDefault())) togetherWith
                    fadeOut(animationSpec = motion(JawharMotion.effectsFast()))
            } else {
                val forward = nav.isForward
                if (forward) {
                    (slideInHorizontally(animationSpec = motion(JawharMotion.spatialDefault())) { fullWidth -> fullWidth / 4 } +
                        fadeIn(animationSpec = motion(JawharMotion.effectsDefault()))) togetherWith
                        (slideOutHorizontally(animationSpec = motion(JawharMotion.spatialFast())) { fullWidth -> -fullWidth / 6 } +
                        fadeOut(animationSpec = motion(JawharMotion.effectsFast())))
                } else {
                    (slideInHorizontally(animationSpec = motion(JawharMotion.spatialDefault())) { fullWidth -> -fullWidth / 6 } +
                        fadeIn(animationSpec = motion(JawharMotion.effectsDefault()))) togetherWith
                        (slideOutHorizontally(animationSpec = motion(JawharMotion.spatialFast())) { fullWidth -> fullWidth / 4 } +
                        fadeOut(animationSpec = motion(JawharMotion.effectsFast())))
                }
            }
        },
    ) { id ->
        val spec = activeCatalog[id]
        if (spec != null) spec.content()
    }
}

@Composable
private fun PhoneHost(nav: JNav) {
    val top = WindowInsets.statusBars.asPaddingValues().calculateTopPadding()
    val bottom = WindowInsets.navigationBars.asPaddingValues().calculateBottomPadding()
    CompositionLocalProvider(LocalTopInset provides top, LocalBottomInset provides bottom) {
        ScreenHost(nav)
    }
}

@Composable
private fun DesktopShell(nav: JNav, windowHeight: Dp) {
    val c = Jawhar.colors
    Row(Modifier.fillMaxSize()) {
        if (AppState.galleryEnabled) {
            GalleryPanel(nav, Modifier.width(300.dp).fillMaxHeight())
        }
        Box(Modifier.weight(1f).fillMaxHeight().background(c.bgSurfaceVariant), contentAlignment = Alignment.Center) {
            val spec = activeCatalog[nav.current]
            if (spec != null && spec.wide) {
                Box(Modifier.fillMaxSize()) { ScreenHost(nav) }
            } else {
                val h = minOf(844.dp, windowHeight - 32.dp)
                Box(Modifier.size(390.dp, h).clip(SquircleShape(44.dp)).background(c.bgBase)) {
                    CompositionLocalProvider(LocalTopInset provides 44.dp, LocalBottomInset provides 24.dp) {
                        ScreenHost(nav)
                    }
                    JText("9:41", Jawhar.type.labelL, c.onSurface, Modifier.align(Alignment.TopStart).padding(start = 24.dp, top = 12.dp))
                }
            }
        }
    }
}

@Composable
private fun LocalBackendIndicator() {
    val c = Jawhar.colors
    val t = Jawhar.type
    Box(
        Modifier
            .fillMaxSize()
            .padding(12.dp),
        contentAlignment = Alignment.BottomStart,
    ) {
        Box(
            Modifier
                .clip(SquircleShape(16.dp))
                .background(c.infoContainer)
                .padding(horizontal = 8.dp, vertical = 4.dp),
        ) {
            Row(
                Modifier.padding(horizontal = 6.dp, vertical = 2.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(4.dp),
            ) {
                JIcon(JI.Info, size = 10.dp, tint = c.info)
                JText("Local backend", t.labelS, c.info)
            }
        }
    }
}
