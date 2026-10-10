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
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.unit.dp
import com.meher.jawhar.data.LocalApi
import com.meher.jawhar.data.api.SrsCardDto
import com.meher.jawhar.data.api.DeckDto
import com.meher.jawhar.data.api.srsDue
import com.meher.jawhar.data.api.srsReview
import com.meher.jawhar.data.api.getDecks
import com.meher.jawhar.design.*
import com.meher.jawhar.nav.Dest
import com.meher.jawhar.nav.LocalNav
import kotlinx.coroutines.launch

@Composable
fun FlashcardScreen(showBack: Boolean = false) {
    val nav = LocalNav.current
    val api = LocalApi.current
    val c = Jawhar.colors
    val t = Jawhar.type

    var queue by remember { mutableStateOf<List<SrsCardDto>>(emptyList()) }
    var index by remember { mutableStateOf(0) }
    var back by remember { mutableStateOf(showBack) }
    var loading by remember { mutableStateOf(true) }
    var submitting by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()

    LaunchedEffect(Unit) {
        try { queue = api.srsDue() } catch (e: Exception) { } finally { loading = false }
    }

    val total = queue.size
    val card = queue.getOrNull(index)

    Page(
        backIcon = JI.Close,
        title = if (loading) "…" else "${index + 1} / $total",
        right = JI.More,
        scroll = false,
        cta = {
            when {
                loading -> JSkeleton(Modifier.fillMaxWidth().height(56.dp), radius = 30.dp)
                card == null -> JButton("Done", { nav.reset(Dest.Home) })
                !back -> JButton("Show answer", { back = true })
                else -> Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    JRating.values().forEach { r ->
                        JRatingButton(r, {
                            if (submitting) return@JRatingButton
                            val cardId = card.id
                            val rating = r.ordinal + 1
                            if (index + 1 >= total) {
                                nav.go(Dest.ReviewDone)
                            } else {
                                index++
                                back = false
                            }
                            submitting = true
                            scope.launch {
                                try { api.srsReview(cardId, rating) } catch (e: Exception) { } finally { submitting = false }
                            }
                        }, Modifier.weight(1f))
                    }
                }
            }
        },
    ) {
        if (loading) {
            JSkeleton(Modifier.fillMaxWidth().height(520.dp), radius = 48.dp)
        } else if (card == null) {
            JCenterState(JI.Check, c.successContainer, c.success, "Queue empty", "All cards reviewed. Come back tomorrow!")
        } else {
            Box(
                Modifier.fillMaxWidth().height(520.dp).clip(SquircleShape(48.dp)).background(if (back) c.bgSurfaceVariant else c.primaryContainer)
                    .starOrnaments(c.primary, StarSpec(171.dp, 260.dp, 520.dp, 0.12f), StarSpec(330.dp, 500.dp, 240.dp, 0.1f))
                    .tappable { back = !back },
            ) {
                if (!back) {
                    Row(Modifier.fillMaxWidth().padding(24.dp), horizontalArrangement = Arrangement.SpaceBetween) {
                        JTag(if (card.new_card) "New word" else "Review")
                        if (card.word_pos_tag != null) JTag(card.word_pos_tag)
                    }
                    Column(Modifier.align(Alignment.Center), horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        JArabic(card.front, t.arabicWordXL, c.onPrimaryContainer)
                        if (card.transliteration != null) JText(card.transliteration, t.translit, c.onPrimaryContainer.copy(alpha = 0.8f))
                    }
                    Column(Modifier.align(Alignment.BottomCenter).padding(bottom = 32.dp), horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(6.dp)) {
                        JIcon(JI.Refresh, size = 22.dp, tint = c.onPrimaryContainer.copy(alpha = 0.7f))
                        JText("Tap the card to reveal", t.labelM, c.onPrimaryContainer.copy(alpha = 0.8f))
                    }
                } else {
                    Column(Modifier.fillMaxSize().padding(24.dp), horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(10.dp)) {
                        JArabic(card.front, t.arabicWordL, c.onSurface)
                        JText(card.back, t.headlineM, c.onSurface)
                        Spacer(Modifier.height(6.dp))
                        listOf("Root" to (card.word_root ?: "—"), "Pattern" to (card.word_pattern ?: "—")).forEach { (a, b) ->
                            Row(Modifier.fillMaxWidth().padding(horizontal = 12.dp)) {
                                JText(a, t.labelM, c.onSurfaceSubtle, Modifier.weight(1f))
                                JText(b, t.titleS, c.onSurface)
                            }
                        }
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
    val api = LocalApi.current
    val c = Jawhar.colors
    val t = Jawhar.type
    var seg by remember { mutableStateOf(0) }
    var decks by remember { mutableStateOf<List<DeckDto>>(emptyList()) }
    var dueCount by remember { mutableStateOf(0) }
    var loading by remember { mutableStateOf(true) }

    LaunchedEffect(Unit) {
        try {
            decks = api.getDecks()
            dueCount = api.srsDue().size
        } catch (e: Exception) { } finally { loading = false }
    }

    Page(back = false, tab = JTab.Learn, right = JI.Search) {
        JText("Vocabulary", t.headlineL, c.onSurface)
        JSegmented(listOf("By frequency", "By root family"), seg, { seg = it })
        HeroCard(stars = listOf(StarSpec(340.dp, 10.dp, 160.dp, 0.26f)), radius = 30.dp, padding = 20.dp) {
            JText("DUE TODAY", t.labelS, c.accent)
            JText(if (loading) "… cards ready" else "$dueCount cards ready", t.headlineS, c.onPrimary)
            JButton("Start review", { nav.go(Dest.FlashFront) }, Modifier.padding(top = 12.dp).width(120.dp), JButtonStyle.Accent, height = 32.dp)
        }
        if (loading) {
            repeat(3) { JSkeleton(Modifier.fillMaxWidth().height(72.dp), radius = 28.dp) }
        } else {
            decks.forEach { d ->
                Row(Modifier.fillMaxWidth().clip(SquircleShape(28.dp)).background(c.bgSurfaceVariant).padding(16.dp), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(14.dp)) {
                    Box(Modifier.size(44.dp).clip(SquircleShape(14.dp)).background(c.primaryContainer), contentAlignment = Alignment.Center) { JIcon(JI.Cards, size = 22.dp, tint = c.onPrimaryContainer) }
                    Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                        JText(d.name, t.titleM, c.onSurface)
                        JText("${d.card_count} cards", t.bodyS, c.onSurfaceVariant)
                    }
                    JTag("${d.due_count} due", background = if (d.due_count == 0) c.successContainer else c.accentContainer, color = if (d.due_count == 0) c.success else c.onAccentContainer, height = 28.dp)
                }
            }
        }
    }
}
