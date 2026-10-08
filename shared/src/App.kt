package com.meher.jawhar

import androidx.compose.animation.Crossfade
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.meher.jawhar.design.*
import com.meher.jawhar.nav.Dest
import com.meher.jawhar.nav.JNav
import com.meher.jawhar.nav.LocalNav
import com.meher.jawhar.screens.GalleryPanel
import com.meher.jawhar.screens.Screens
import org.jetbrains.compose.reload.DevelopmentEntryPoint

@Composable
@Preview
@DevelopmentEntryPoint
fun App() {
    JawharTheme {
        val nav = remember { JNav(Dest.Splash) }
        CompositionLocalProvider(LocalNav provides nav) {
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

@Composable
private fun ScreenHost(nav: JNav) {
    Crossfade(targetState = nav.current, label = "screen") { id ->
        val spec = Screens.byId[id]
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
        GalleryPanel(nav, Modifier.width(300.dp).fillMaxHeight())
        Box(Modifier.weight(1f).fillMaxHeight().background(c.bgSurfaceVariant), contentAlignment = Alignment.Center) {
            val spec = Screens.byId[nav.current]
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
