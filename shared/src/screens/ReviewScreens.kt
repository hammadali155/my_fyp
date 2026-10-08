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
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.unit.dp
import com.meher.jawhar.design.*
import com.meher.jawhar.nav.Dest
import com.meher.jawhar.nav.LocalNav

@Composable
fun FlashcardScreen(showBack: Boolean = false) {
    val nav = LocalNav.current
    val c = Jawhar.colors
    val t = Jawhar.type
    var back by remember { mutableStateOf(showBack) }
    Page(
        backIcon = JI.Close,
        title = "12 / 15",
        right = JI.More,
        scroll = false,
        cta = {
            if (!back) {
                JButton("Show answer", { back = true })
            } else {
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    JRating.values().forEach { r -> JRatingButton(r, { back = false; if (r == JRating.Easy) nav.go(Dest.ReviewDone) }, Modifier.weight(1f)) }
                }
            }
        },
    ) {
        Box(
            Modifier.fillMaxWidth().height(520.dp).clip(SquircleShape(48.dp)).background(if (back) c.bgSurfaceVariant else c.primaryContainer)
                .starOrnaments(c.primary, StarSpec(171.dp, 260.dp, 520.dp, 0.12f), StarSpec(330.dp, 500.dp, 240.dp, 0.1f))
                .tappable { back = !back },
        ) {
            if (!back) {
                Row(Modifier.fillMaxWidth().padding(24.dp), horizontalArrangement = Arrangement.SpaceBetween) {
                    JTag("New word")
                    JTag("Noun")
                }
                Column(Modifier.align(Alignment.Center), horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    JArabic("كِتَابٌ", t.arabicWordXL, c.onPrimaryContainer)
                    JText("kitābun", t.translit, c.onPrimaryContainer.copy(alpha = 0.8f))
                }
                Column(Modifier.align(Alignment.BottomCenter).padding(bottom = 32.dp), horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    JIcon(JI.Refresh, size = 22.dp, tint = c.onPrimaryContainer.copy(alpha = 0.7f))
                    JText("Tap the card to reveal", t.labelM, c.onPrimaryContainer.copy(alpha = 0.8f))
                }
            } else {
                Column(Modifier.fillMaxSize().padding(24.dp), horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    JArabic("كِتَابٌ", t.arabicWordL, c.onSurface)
                    JText("book", t.headlineM, c.onSurface)
                    Spacer(Modifier.height(6.dp))
                    listOf("Root" to "ك ت ب", "Pattern" to "فِعَالٌ", "Form" to "Noun").forEach { (a, b) ->
                        Row(Modifier.fillMaxWidth().padding(horizontal = 12.dp)) {
                            JText(a, t.labelM, c.onSurfaceSubtle, Modifier.weight(1f))
                            JText(b, t.titleS, c.onSurface)
                        }
                    }
                    Spacer(Modifier.height(6.dp))
                    JCard(Modifier.fillMaxWidth(), color = c.bgSurface, padding = 20.dp) {
                        JText("IN THE QURAN", t.labelS, c.onSurfaceSubtle)
                        Spacer(Modifier.height(8.dp))
                        AyahWords(listOf("ذَٰلِكَ", "ٱلْكِتَٰبُ", "لَا", "رَيْبَ", "فِيهِ"), listOf(1), highlightColor = c.accentContainer)
                        JText("This is the Book, with no doubt in it.", t.bodyS, c.onSurface)
                        Spacer(Modifier.height(6.dp))
                        JText("Al-Baqarah 2:2", t.labelM, c.onSurfaceSubtle)
                    }
                }
            }
        }
    }
}

@Composable
fun ReviewCompleteScreen() {
    val nav = LocalNav.current
    val c = Jawhar.colors
    val t = Jawhar.type
    Page(back = false, cta = { JButton("Done", { nav.reset(Dest.Home) }) }) {
        Box(Modifier.fillMaxWidth().padding(top = 8.dp), contentAlignment = Alignment.Center) {
            Box(Modifier.size(330.dp).starOrnaments(c.accent, StarSpec(165.dp, 165.dp, 330.dp, 0.3f)), contentAlignment = Alignment.Center) {
                JProgressRing(0.87f, size = 168.dp) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        JText("87%", t.headlineL, c.onSurface)
                        JText("remembered", t.labelM, c.onSurfaceVariant)
                    }
                }
            }
        }
        BigTitle("Session complete", "You reviewed 15 cards in 5 minutes.", center = true)
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(9.dp)) {
            JStatTile(JI.Cards, "15", "Reviewed", c.primaryContainer, c.onPrimaryContainer, Modifier.weight(1f))
            JStatTile(JI.Check, "13", "Good or Easy", c.successContainer, c.success, Modifier.weight(1f))
            JStatTile(JI.Refresh, "2", "To retry", c.accentContainer, c.onAccentContainer, Modifier.weight(1f))
        }
        JInfoCard("Next review tomorrow", "8 cards are scheduled for 8:00 AM. Keep your streak going.", tone = JTone.Info, icon = JI.Calendar)
    }
}

@Composable
fun VocabularyScreen() {
    val nav = LocalNav.current
    val c = Jawhar.colors
    val t = Jawhar.type
    var seg by remember { mutableStateOf(0) }
    Page(back = false, tab = JTab.Learn, right = JI.Search) {
        JText("Vocabulary", t.headlineL, c.onSurface)
        JSegmented(listOf("By frequency", "By root family"), seg, { seg = it })
        HeroCard(stars = listOf(StarSpec(340.dp, 10.dp, 160.dp, 0.26f)), radius = 30.dp, padding = 20.dp) {
            JText("DUE TODAY", t.labelS, c.accent)
            JText("15 cards ready", t.headlineS, c.onPrimary)
            JButton("Start review", { nav.go(Dest.FlashFront) }, Modifier.padding(top = 12.dp).width(120.dp), JButtonStyle.Accent, height = 32.dp)
        }
        Mock.decks.forEach { d ->
            Row(Modifier.fillMaxWidth().clip(SquircleShape(28.dp)).background(c.bgSurfaceVariant).padding(16.dp), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(14.dp)) {
                Box(Modifier.size(44.dp).clip(SquircleShape(14.dp)).background(c.primaryContainer), contentAlignment = Alignment.Center) { JIcon(JI.Cards, size = 22.dp, tint = c.onPrimaryContainer) }
                Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    JText(d.title, t.titleM, c.onSurface)
                    JText(d.sub, t.bodyS, c.onSurfaceVariant)
                    JProgressBar(d.progress, height = 6.dp, track = c.bgSurfaceHigh)
                }
                JTag(d.due, background = if (d.due == "Done") c.successContainer else c.accentContainer, color = if (d.due == "Done") c.success else c.onAccentContainer, height = 28.dp)
            }
        }
    }
}
