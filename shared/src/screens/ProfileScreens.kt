package com.meher.jawhar.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
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
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.meher.jawhar.design.*
import com.meher.jawhar.nav.Dest
import com.meher.jawhar.nav.LocalNav

@Composable
fun ProgressScreen() {
    val c = Jawhar.colors
    val t = Jawhar.type
    Page {
        JText("Progress", t.headlineL, c.onSurface)
        HeroCard(color = c.primaryContainer, starColor = c.primary, stars = listOf(StarSpec(340.dp, 10.dp, 180.dp, 0.22f)), radius = 34.dp, padding = 20.dp) {
            JText("YOUR LEVEL", t.labelS, c.onPrimaryContainer.copy(alpha = 0.8f))
            JText("Beginner II", t.headlineM, c.onSurface)
            Row(Modifier.fillMaxWidth().padding(top = 8.dp), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                JProgressBar(0.66f, Modifier.weight(1f), track = c.bgSurface)
                JText("340 XP to Beginner III", t.bodyS, c.onPrimaryContainer)
            }
        }
        JCard(Modifier.fillMaxWidth(), radius = 34.dp, padding = 20.dp) {
            Row(Modifier.fillMaxWidth()) {
                JText("This week", t.titleM, c.onSurface, Modifier.weight(1f))
                JText("34 min · 5 days", t.labelL, c.onSurfaceVariant)
            }
            Row(Modifier.fillMaxWidth().padding(top = 16.dp).height(150.dp), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.Bottom) {
                Mock.weekMinutes.forEachIndexed { i, m ->
                    Column(Modifier.weight(1f), horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        Box(Modifier.size(28.dp, (if (m == 0) 28 else maxOf(28, m * 6)).dp).clip(CapsuleShape).background(if (i == 5) c.accent else if (m > 0) c.primary else c.bgSurfaceHigh))
                        JText(Mock.weekDays[i], t.labelM, if (i == 5) c.onSurface else c.onSurfaceSubtle)
                    }
                }
            }
        }
        JCard(Modifier.fillMaxWidth(), radius = 34.dp, padding = 20.dp) {
            JText("Topic mastery", t.titleM, c.onSurface)
            Spacer(Modifier.height(12.dp))
            listOf("Vocabulary" to listOf(0.9f, 0.8f, 0.7f, 0.5f, 0.35f, 0.2f), "Sarf" to listOf(0.8f, 0.6f, 0.4f, 0.3f, 0.15f, 0.1f), "Nahw" to listOf(0.6f, 0.4f, 0.25f, 0.15f, 0.1f, 0.05f)).forEach { (label, vals) ->
                Row(Modifier.fillMaxWidth().padding(vertical = 5.dp), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    JText(label, t.labelL, c.onSurfaceVariant, Modifier.weight(2.4f))
                    vals.forEach { v -> Box(Modifier.weight(1f).height(32.dp).clip(SquircleShape(11.dp)).background(c.primary.copy(alpha = 0.12f + 0.88f * v))) }
                }
            }
        }
    }
}

@Composable
fun LeaderboardScreen() {
    val c = Jawhar.colors
    val t = Jawhar.type
    Page(
        cta = {
            Row(
                Modifier.fillMaxWidth().softShadow(SquircleShape(28.dp), 14.dp, 0.3f).clip(SquircleShape(28.dp)).background(c.primaryContainer).padding(horizontal = 16.dp, vertical = 16.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                JText("9", t.titleM, c.onPrimaryContainer, Modifier.size(32.dp), TextAlign.Center)
                JAvatar("MA", size = 40.dp)
                JText("You", t.titleS, c.onSurface, Modifier.weight(1f))
                JText("2,480 XP", t.labelL, c.onPrimaryContainer)
            }
        },
    ) {
        JText("Leaderboard", t.headlineL, c.onSurface)
        JTag("Resets Monday · 3 days", background = c.accentContainer, color = c.onAccentContainer, icon = JI.Clock, height = 36.dp)
        Row(Modifier.fillMaxWidth().padding(vertical = 8.dp), horizontalArrangement = Arrangement.SpaceEvenly, verticalAlignment = Alignment.Bottom) {
            listOf(Triple("Hammad A.", "2,910 XP", 2), Triple("Sara K.", "3,240 XP", 1), Triple("Bilal R.", "2,760 XP", 3)).forEach { (n, xp, rank) ->
                val size = if (rank == 1) 72.dp else 56.dp
                Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(4.dp), modifier = Modifier.padding(bottom = if (rank == 1) 24.dp else 0.dp)) {
                    Box {
                        JAvatar(n.take(1) + n.substringAfter(" ").take(1), size = size)
                        Box(Modifier.align(Alignment.BottomEnd).size(22.dp).clip(CircleShape).background(if (rank == 1) c.accent else c.bgSurfaceHigh), contentAlignment = Alignment.Center) {
                            JText(rank.toString(), t.labelM, c.onSurface)
                        }
                    }
                    JText(n, t.titleS, c.onSurface)
                    JText(xp, t.labelM, c.onSurfaceVariant)
                }
            }
        }
        Mock.leaders.forEach { r ->
            Row(Modifier.fillMaxWidth().clip(SquircleShape(24.dp)).background(c.bgSurfaceVariant).padding(horizontal = 16.dp, vertical = 12.dp), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                JText(r.rank.toString(), t.titleM, c.onSurfaceVariant, Modifier.size(32.dp), TextAlign.Center)
                JAvatar(r.initials, size = 40.dp)
                JText(r.name, t.titleS, c.onSurface, Modifier.weight(1f))
                JText(r.xp, t.labelL, c.onSurfaceVariant)
            }
        }
    }
}

@Composable
fun BadgesScreen() {
    val c = Jawhar.colors
    val t = Jawhar.type
    var filter by remember { mutableStateOf(0) }
    Page {
        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
            JText("Badges", t.headlineL, c.onSurface, Modifier.weight(1f))
            JText("12 of 30+", t.labelL, c.onSurfaceVariant)
        }
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) { listOf("All", "Unlocked", "Locked").forEachIndexed { i, l -> JChip(l, filter == i, { filter = i }) } }
        Mock.badges.filter { filter == 0 || (filter == 1 && it.unlocked) || (filter == 2 && !it.unlocked) }.chunked(3).forEach { row ->
            Row(Modifier.fillMaxWidth()) {
                row.forEach { JBadgeTile(it.title, it.caption, it.unlocked, Modifier.weight(1f)) }
                repeat(3 - row.size) { Spacer(Modifier.weight(1f)) }
            }
        }
    }
}

@Composable
fun ProfileScreen() {
    val nav = LocalNav.current
    val c = Jawhar.colors
    val t = Jawhar.type
    Page(back = false, tab = JTab.Profile, right = JI.Sliders, onRight = { nav.go(Dest.Settings) }) {
        Column(Modifier.fillMaxWidth(), horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Box(Modifier.size(190.dp).starOrnaments(c.accent, StarSpec(95.dp, 95.dp, 190.dp, 0.3f)), contentAlignment = Alignment.Center) { JAvatar("MA", size = 88.dp) }
            JText("Meher Ali", t.headlineM, c.onSurface)
            JText("Beginner II · Joined Oct 2026", t.bodyM, c.onSurfaceVariant)
        }
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(9.dp)) {
            JStatTile(JI.Flame, "12", "Day streak", c.accentContainer, c.onAccentContainer, Modifier.weight(1f))
            JStatTile(JI.Bolt, "2,480", "Total XP", c.primaryContainer, c.onPrimaryContainer, Modifier.weight(1f))
            JStatTile(JI.Cards, "342", "Words learned", c.infoContainer, c.info, Modifier.weight(1f))
        }
        JListItem("Progress", subtitle = "Weekly activity and topic mastery", icon = JI.Chart, onClick = { nav.go(Dest.Progress) })
        JListItem("Leaderboard", subtitle = "Rank 9 this week", icon = JI.Trophy, onClick = { nav.go(Dest.Leaderboard) })
        JListItem("Badges", subtitle = "12 of 30+ unlocked", icon = JI.Star, onClick = { nav.go(Dest.Badges) })
        JListItem("Bookmarks", subtitle = "23 saved ayat and words", icon = JI.Bookmark, onClick = { nav.go(Dest.Quran) })
    }
}

@Composable
fun SettingsScreen(showLogout: Boolean = false, showDelete: Boolean = false) {
    val nav = LocalNav.current
    val c = Jawhar.colors
    val t = Jawhar.type
    var reminders by remember { mutableStateOf(true) }
    var logout by remember { mutableStateOf(showLogout) }
    var delete by remember { mutableStateOf(showDelete) }
    Page(overlay = {
        if (logout) JDialog("Log out?", "You can log back in at any time. Your progress is saved to your account.", "Log out", { nav.reset(Dest.GetStarted) }, { logout = false }, icon = JI.Logout)
        if (delete) JDialog("Delete your account?", "All progress, streaks and bookmarks will be permanently removed. This cannot be undone.", "Delete", { nav.reset(Dest.GetStarted) }, { delete = false }, icon = JI.Trash, destructive = true)
    }) {
        JText("Settings", t.headlineL, c.onSurface)
        JSectionLabel("Account")
        JListItem("Edit profile", icon = JI.User, onClick = { nav.go(Dest.EditProfile) })
        JListItem("Password", icon = JI.Lock, onClick = { nav.go(Dest.Forgot) })
        JSectionLabel("Learning")
        JListItem("Daily goal", icon = JI.Target, trailing = { JText("10 min", t.labelL, c.onSurfaceVariant); JIcon(JI.Chevron, size = 20.dp, tint = c.onSurfaceSubtle) }, onClick = { nav.go(Dest.DailyGoal) })
        JListItem("Reminders", icon = JI.Bell, trailing = { JSwitch(reminders, { reminders = it }) }, onClick = { nav.go(Dest.NotifSettings) })
        JSectionLabel("Appearance")
        JListItem("Theme", icon = JI.Moon, trailing = { JText("System", t.labelL, c.onSurfaceVariant); JIcon(JI.Chevron, size = 20.dp, tint = c.onSurfaceSubtle) }, onClick = { nav.go(Dest.Appearance) })
        JListItem("Reading options", icon = JI.Sliders, onClick = { nav.go(Dest.Appearance) })
        JSectionLabel("More")
        JListItem("Help and About", icon = JI.Help, onClick = { nav.go(Dest.Help) })
        JListItem("Log out", icon = JI.Logout, tile = c.errorContainer, tileTint = c.error, onClick = { logout = true })
        JListItem("Delete account", icon = JI.Trash, tile = c.errorContainer, tileTint = c.error, onClick = { delete = true })
    }
}

@Composable
fun EditProfileScreen() {
    val nav = LocalNav.current
    val c = Jawhar.colors
    Page(cta = { JButton("Save changes", { nav.back() }) }) {
        BigTitle("Edit profile")
        Box(Modifier.fillMaxWidth(), contentAlignment = Alignment.Center) {
            JAvatar("MA", size = 96.dp)
            Box(Modifier.align(Alignment.BottomCenter).padding(start = 72.dp).size(32.dp).clip(CircleShape).background(c.primary), contentAlignment = Alignment.Center) { JIcon(JI.Edit, size = 16.dp, tint = c.onPrimary) }
        }
        StatefulField("Full name", "Meher Ali", trailing = JI.User)
        StatefulField("Email", "meher@email.com", helper = "Email cannot be changed", trailing = JI.Mail)
        StatefulField("Daily goal", "10 minutes", trailing = JI.Target)
    }
}

@Composable
fun AppearanceScreen() {
    val c = Jawhar.colors
    val t = Jawhar.type
    var theme by remember { mutableStateOf(1) }
    var size by remember { mutableStateOf(0.6f) }
    var translit by remember { mutableStateOf(true) }
    var translation by remember { mutableStateOf(true) }
    Page {
        BigTitle("Appearance")
        JSectionLabel("Theme")
        JSegmented(listOf("System", "Light", "Dark"), theme, { theme = it })
        JSectionLabel("Arabic text size")
        JSlider(size, { size = it })
        JCard(Modifier.fillMaxWidth(), radius = 34.dp, padding = 20.dp) {
            JArabic("ٱلْحَمْدُ لِلَّهِ رَبِّ ٱلْعَٰلَمِينَ", t.arabicQuranL.copy(fontSize = (22 + 24 * size).sp, lineHeight = (40 + 40 * size).sp), c.onSurface, Modifier.fillMaxWidth())
            if (translit) JText("Al-ḥamdu lillāhi rabbil-’ālamīn", t.translit, c.onSurfaceVariant)
            if (translation) JText("Praise belongs to God, Lord of all the worlds.", t.bodyM, c.onSurface, Modifier.padding(top = 4.dp))
        }
        JListItem("Show transliteration", icon = JI.Doc, trailing = { JSwitch(translit, { translit = it }) })
        JListItem("Show translation", icon = JI.Globe, trailing = { JSwitch(translation, { translation = it }) })
        JListItem("App language", icon = JI.Globe, trailing = { JText("English", t.labelL, c.onSurfaceVariant); JIcon(JI.Chevron, size = 20.dp, tint = c.onSurfaceSubtle) })
    }
}

@Composable
fun NotificationSettingsScreen() {
    val c = Jawhar.colors
    val t = Jawhar.type
    val items = listOf(
        Triple("Daily reminder", "Every day at 8:00 PM", JI.Bell), Triple("Streak reminders", "Before your streak ends", JI.Flame), Triple("Daily challenge", "When a new one is ready", JI.Target),
        Triple("Leaderboard updates", "Weekly results on Monday", JI.Trophy), Triple("Product news", "New features and tips", JI.Info),
    )
    val states = remember { mutableStateOf(listOf(true, true, true, false, false)) }
    Page {
        BigTitle("Notifications")
        items.forEachIndexed { i, (title, sub, ic) ->
            JListItem(title, subtitle = sub, icon = ic, trailing = { JSwitch(states.value[i], { v -> states.value = states.value.toMutableList().also { it[i] = v } }) })
        }
        JListItem("Reminder time", icon = JI.Clock, trailing = { JText("8:00 PM", t.labelL, c.onSurfaceVariant); JIcon(JI.Chevron, size = 20.dp, tint = c.onSurfaceSubtle) })
        JInfoCard("Quiet hours", "Reminders follow your phone Do Not Disturb settings.", icon = JI.Moon)
    }
}

@Composable
fun HelpAboutScreen() {
    val c = Jawhar.colors
    val t = Jawhar.type
    Page {
        BigTitle("Help and About")
        JSectionLabel("Common questions")
        JListItem("How is a word root found?", icon = JI.Tree)
        JListItem("What do the colours mean?", icon = JI.Layers)
        JListItem("How do reviews work?", icon = JI.Cards)
        JListItem("Contact support", icon = JI.Mail)
        Row(Modifier.fillMaxWidth().clip(SquircleShape(30.dp)).background(c.bgSurfaceVariant).padding(16.dp), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(14.dp)) {
            JLogoMark(size = 56.dp)
            Column {
                JText("Jawhar", t.titleM, c.onSurface)
                JText("Version 1.0.0", t.bodyS, c.onSurfaceVariant)
            }
        }
        JInfoCard("Built on open resources", "CAMeL Tools for morphology, Farasa for syntax, and the Quranic Arabic Corpus for word data.", tone = JTone.Info, icon = JI.Info)
        JListItem("Terms and Privacy", icon = JI.Shield)
    }
}
