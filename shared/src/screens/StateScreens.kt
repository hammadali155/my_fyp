package com.meher.jawhar.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.meher.jawhar.design.*
import com.meher.jawhar.nav.Dest
import com.meher.jawhar.nav.LocalNav

@Composable
fun SessionExpiredScreen() {
    val nav = LocalNav.current
    Box(Modifier.fillMaxSize()) {
        HomeScreen()
        JDialog("Session expired", "For your security, please log in again. Your progress is saved.", "Log in", { nav.reset(Dest.LogIn) }, {}, cancel = "Later", icon = JI.Lock)
    }
}

@Composable
fun NoInternetScreen() {
    val c = Jawhar.colors
    StateScreen(JI.WifiOff, c.bgSurfaceVariant, c.onSurfaceVariant, "No internet connection", "Jawhar needs a connection to analyse words and sync your progress.", "Try again", "Go to settings")
}

@Composable
fun OfflineBannerScreen() {
    Box(Modifier.fillMaxSize()) {
        HomeScreen()
        Box(Modifier.padding(top = LocalTopInset.current + 60.dp, start = 24.dp, end = 24.dp)) {
            JBanner(JBannerKind.Offline, "You're offline", "Reconnect to keep learning. Your progress is safe.", floating = true)
        }
    }
}

@Composable
fun ServerErrorScreen() {
    val c = Jawhar.colors
    StateScreen(JI.Alert, c.errorContainer, c.error, "Something went wrong on our side", "We are looking into it. Please try again in a moment.", "Try again", "Report a problem")
}

@Composable
fun NotFoundScreen() {
    val nav = LocalNav.current
    val c = Jawhar.colors
    Page(
        scroll = false,
        cta = {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                JButton("Back to Home", { nav.reset(Dest.Home) })
                JButton("Search", { nav.go(Dest.Search) }, style = JButtonStyle.Neutral)
            }
        },
    ) {
        Column(Modifier.fillMaxWidth().padding(top = 80.dp), horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(16.dp)) {
            Box(Modifier.size(280.dp).starOrnaments(c.accent, StarSpec(140.dp, 140.dp, 280.dp, 0.3f)), contentAlignment = Alignment.Center) {
                JText("404", Jawhar.type.displayL, c.primary)
            }
            BigTitle("We could not find that page", "The ayah or lesson may have moved. Try searching instead.", center = true)
        }
    }
}

@Composable
fun MaintenanceScreen() {
    val c = Jawhar.colors
    StateScreen(JI.Refresh, c.accentContainer, c.onAccentContainer, "Back soon", "We are improving the analyser. This usually takes a few minutes.", "Check again")
}

@Composable
fun UpdateRequiredScreen() {
    val c = Jawhar.colors
    StateScreen(JI.Download, c.primaryContainer, c.primary, "Update required", "A new version is available with important fixes. Please update to continue.", "Update app")
}

@Composable
fun EmptyBookmarksScreen() {
    val nav = LocalNav.current
    val c = Jawhar.colors
    Page(back = false, tab = JTab.Quran, right = JI.Bookmark) {
        JText("Quran", Jawhar.type.headlineL, c.onSurface)
        JSearchField("", {}, "Search surah, ayah or word")
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) { listOf("Surahs", "Juz", "Bookmarks").forEachIndexed { i, l -> JChip(l, i == 2, {}) } }
        Spacer(Modifier.height(24.dp))
        JCenterState(JI.Bookmark, c.primaryContainer, c.primary, "No bookmarks yet", "Tap the bookmark on any ayah to save it here.")
        JButton("Browse the Quran", { nav.reset(Dest.Quran) }, Modifier.align(Alignment.CenterHorizontally).width(170.dp), JButtonStyle.Tonal, height = 44.dp)
    }
}

@Composable
fun AllCaughtUpScreen() {
    val nav = LocalNav.current
    val c = Jawhar.colors
    StateScreen(JI.Check, c.successContainer, c.success, "All caught up", "No cards are due right now. Your next review is in 4 hours.", "Learn new words", "Back to Home", onPrimary = { nav.reset(Dest.Learn) }, onSecondary = { nav.reset(Dest.Home) })
}

@Composable
fun SkeletonHomeScreen() {
    Page(back = false, tab = JTab.Home, scroll = false) {
        JSkeleton(Modifier.size(140.dp, 18.dp), 9.dp)
        JSkeleton(Modifier.size(120.dp, 34.dp), 12.dp)
        JSkeleton(Modifier.fillMaxWidth().height(216.dp), 34.dp, Jawhar.colors.outlineVariant)
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(9.dp)) { repeat(3) { JSkeleton(Modifier.weight(1f).height(102.dp), 26.dp) } }
        JSkeleton(Modifier.fillMaxWidth().height(92.dp), 30.dp)
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(9.dp)) { repeat(3) { JSkeleton(Modifier.weight(1f).height(104.dp), 26.dp) } }
    }
}

@Composable
fun SkeletonReaderScreen() {
    Page(title = "Al-Fatiha", right = JI.More, scroll = false, spacing = 28.dp) {
        repeat(3) {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Row(horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.CenterVertically) {
                    JSkeleton(Modifier.size(32.dp), 16.dp)
                    JSkeleton(Modifier.weight(1f).height(20.dp), 10.dp)
                }
                JSkeleton(Modifier.fillMaxWidth(0.55f).height(14.dp), 7.dp)
                JSkeleton(Modifier.fillMaxWidth().height(14.dp), 7.dp)
                JSkeleton(Modifier.fillMaxWidth(0.7f).height(14.dp), 7.dp)
            }
        }
    }
}

@Composable
fun NotificationsDeniedScreen() {
    val c = Jawhar.colors
    StateScreen(JI.Bell, c.accentContainer, c.onAccentContainer, "Notifications are off", "Turn them on in system settings to protect your streak with a daily reminder.", "Open settings", "Not now", back = true)
}

@Composable
fun StreakAtRiskScreen() {
    Box(Modifier.fillMaxSize()) {
        HomeScreen()
        Box(Modifier.padding(top = LocalTopInset.current + 60.dp, start = 24.dp, end = 24.dp)) {
            JBanner(JBannerKind.Warning, "Your streak ends in 3 hours", "Finish one review to keep your 12 days going.", floating = true)
        }
    }
}

@Composable
fun StreakLostScreen() {
    val nav = LocalNav.current
    Box(Modifier.fillMaxSize()) {
        HomeScreen()
        JDialog("Your streak ended", "Your 12 day streak is over. Start a new one today, every day counts.", "Start again", { nav.go(Dest.FlashFront) }, { nav.reset(Dest.Home) }, cancel = "Dismiss", icon = JI.Flame)
    }
}

@Composable
fun LevelUpScreen() {
    val nav = LocalNav.current
    val c = Jawhar.colors
    Page(back = false, cta = { JButton("Keep going", { nav.reset(Dest.Home) }) }) {
        Box(Modifier.fillMaxWidth().padding(top = 24.dp), contentAlignment = Alignment.Center) {
            Box(Modifier.size(340.dp).starOrnaments(c.accent, StarSpec(170.dp, 170.dp, 340.dp, 0.3f), StarSpec(170.dp, 170.dp, 240.dp, 0.4f)), contentAlignment = Alignment.Center) {
                Box(Modifier.size(156.dp).softShadow(CircleShape, 12.dp, 0.3f).clip(CircleShape).background(c.primary), contentAlignment = Alignment.Center) {
                    JIcon(JI.Spark, size = 68.dp, tint = c.accent, strokeWidth = 1.6.dp)
                }
            }
        }
        BigTitle("Level up", "You reached Beginner III", center = true)
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.Center) { JTag("+200 XP bonus", background = c.accentContainer, color = c.onAccentContainer, height = 36.dp) }
    }
}

@Composable
fun BadgeUnlockedScreen() {
    val nav = LocalNav.current
    val c = Jawhar.colors
    val t = Jawhar.type
    Box(Modifier.fillMaxSize()) {
        HomeScreen()
        JBottomSheet({ nav.reset(Dest.Home) }) {
            Box(Modifier.size(104.dp).starOrnaments(c.accent, StarSpec(52.dp, 52.dp, 100.dp, 0.5f)), contentAlignment = Alignment.Center) {
                Box(Modifier.size(80.dp).softShadow(CircleShape, 12.dp, 0.3f).clip(CircleShape).background(c.accent), contentAlignment = Alignment.Center) { JIcon(JI.Trophy, size = 40.dp, tint = c.onAccent, strokeWidth = 1.6.dp) }
            }
            JText("Badge unlocked", t.labelL, c.primary)
            JText("Root Seeker", t.headlineM, c.onSurface)
            JText("You analysed 50 roots. Keep exploring the Quran word by word.", t.bodyM, c.onSurfaceVariant, textAlign = TextAlign.Center)
            TwoButtons("Share", {}, "Continue", { nav.reset(Dest.Home) })
        }
    }
}

@Composable
fun LogoutDialogScreen() = SettingsScreen(showLogout = true)

@Composable
fun DeleteDialogScreen() = SettingsScreen(showDelete = true)

@Composable
fun LeaveLessonScreen() {
    val nav = LocalNav.current
    Box(Modifier.fillMaxSize()) {
        LessonQuizScreen()
        JDialog("Leave this lesson?", "Your progress in this lesson will be lost. Completed lessons stay saved.", "Leave", { nav.reset(Dest.Learn) }, {}, cancel = "Keep going", icon = JI.Close)
    }
}

@Composable
fun SnackbarsScreen() {
    Box(Modifier.fillMaxSize()) {
        LeaderboardScreen()
        JScrim()
        Column(Modifier.align(Alignment.BottomCenter).padding(start = 24.dp, end = 24.dp, bottom = 120.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            JSnackbar("Added to your review queue", "Undo")
            JSnackbar("Bookmark added", "Undo", kind = JBannerKind.Success)
            JSnackbar("Could not sync progress", "Retry", kind = JBannerKind.Error)
        }
    }
}

@Composable
fun FilterSheetScreen() {
    val c = Jawhar.colors
    val t = Jawhar.type
    var skill by remember { mutableStateOf(1) }
    var status by remember { mutableStateOf(1) }
    var length by remember { mutableStateOf(0) }
    Box(Modifier.fillMaxSize()) {
        LearnPathScreen()
        JBottomSheet({}) {
            JText("Filter lessons", t.headlineS, c.onSurface, Modifier.fillMaxWidth())
            JSectionLabel("Skill")
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) { listOf("Vocabulary", "Sarf", "Nahw").forEachIndexed { i, l -> JChip(l, skill == i, { skill = i }) } }
            JSectionLabel("Status")
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) { listOf("All", "In progress", "Completed").forEachIndexed { i, l -> JChip(l, status == i, { status = i }) } }
            JSectionLabel("Length")
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) { listOf("Under 5 min", "5 to 10 min", "10+ min").forEachIndexed { i, l -> JChip(l, length == i, { length = i }) } }
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                JButton("Show 14 lessons", {}, Modifier.weight(2.4f))
                JButton("Reset", {}, Modifier.weight(1f), JButtonStyle.Neutral)
            }
        }
    }
}
