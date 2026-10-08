package com.meher.jawhar.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.unit.dp
import com.meher.jawhar.design.*
import com.meher.jawhar.nav.Dest
import com.meher.jawhar.nav.LocalNav

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun AyahWords(words: List<String>, highlight: List<Int> = emptyList(), onWord: (Int) -> Unit = {}, highlightColor: Color = Jawhar.colors.primaryContainer) {
    CompositionLocalProvider(LocalLayoutDirection provides LayoutDirection.Rtl) {
        FlowRow(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(2.dp)) {
            words.forEachIndexed { i, w ->
                Box(
                    Modifier.clip(SquircleShape(14.dp)).background(if (i in highlight) highlightColor else Color.Transparent).tappable { onWord(i) }.padding(horizontal = 6.dp),
                ) { JArabic(w, Jawhar.type.arabicQuranL, Jawhar.colors.onSurface) }
            }
        }
    }
}

@Composable
fun AyahBlock(item: AyahItem, highlight: List<Int> = emptyList(), onWord: (Int) -> Unit = {}) {
    val c = Jawhar.colors
    Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            JStarBadge(item.number.toString(), size = 32.dp)
            AyahWords(item.words, highlight, onWord)
        }
        JText(item.translit, Jawhar.type.translit, c.onSurfaceVariant)
        JText(item.english, Jawhar.type.bodyM, c.onSurface)
    }
}

@Composable
fun SurahListScreen() {
    val nav = LocalNav.current
    val c = Jawhar.colors
    val t = Jawhar.type
    var q by remember { mutableStateOf("") }
    var tab by remember { mutableStateOf(0) }
    Page(back = false, tab = JTab.Quran, right = JI.Bookmark) {
        JText("Quran", t.headlineL, c.onSurface)
        JSearchField(q, { q = it }, "Search surah, ayah or word")
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            listOf("Surahs", "Juz", "Bookmarks").forEachIndexed { i, l -> JChip(l, tab == i, { tab = i }) }
        }
        Row(
            Modifier.fillMaxWidth().clip(SquircleShape(30.dp)).background(c.primaryContainer).tappable { nav.go(Dest.Reader) }.padding(20.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                JText("CONTINUE READING", t.labelS, c.onPrimaryContainer.copy(alpha = 0.8f))
                JText("Al-Baqarah · Ayah 142", t.titleM, c.onSurface)
                JProgressBar(0.5f, Modifier.width(200.dp), height = 6.dp, track = c.bgSurface)
            }
            Box(Modifier.size(48.dp).clip(CapsuleShape).background(c.primary), contentAlignment = Alignment.Center) { JIcon(JI.Chevron, size = 20.dp, tint = c.onPrimary, strokeWidth = 2.2.dp) }
        }
        Mock.surahs.filter { q.isBlank() || it.name.contains(q, ignoreCase = true) }.forEach { s ->
            Row(
                Modifier.fillMaxWidth().clip(SquircleShape(26.dp)).background(c.bgSurfaceVariant).tappable { nav.go(Dest.Reader) }.padding(horizontal = 16.dp, vertical = 14.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(14.dp),
            ) {
                JStarBadge(s.number.toString())
                Column(Modifier.weight(1f)) {
                    JText(s.name, t.titleM, c.onSurface)
                    JText(s.meta, t.bodyS, c.onSurfaceVariant)
                }
                JArabic(s.arabic, t.arabicHeading, c.onSurface)
            }
        }
    }
}

@Composable
fun AyahReaderScreen(showPopup: Boolean = false) {
    val nav = LocalNav.current
    val c = Jawhar.colors
    val t = Jawhar.type
    var popup by remember { mutableStateOf(showPopup) }
    Page(
        title = "Al-Fatiha",
        right = JI.More,
        spacing = 28.dp,
        cta = {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(16.dp), verticalAlignment = Alignment.CenterVertically) {
                Row(
                    Modifier.weight(1f).height(56.dp).softShadow(CapsuleShape, 14.dp, 0.3f).clip(CapsuleShape).background(c.bgSurface.copy(alpha = 0.94f)).tappable { nav.go(Dest.NahwResult) }.padding(horizontal = 22.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(12.dp),
                ) {
                    JIcon(JI.Spark, size = 22.dp, tint = c.primary)
                    JText("Analyse verse", t.labelL, c.onSurface, Modifier.weight(1f))
                    JText("Ayah 2", t.labelM, c.onSurfaceSubtle)
                }
                JFloatingButton(JI.Bookmark, {}, size = 56.dp)
            }
        },
        overlay = { if (popup) WordSheet(onDismiss = { popup = false }, onSarf = { popup = false; nav.go(Dest.Sarf) }) },
    ) {
        Mock.ayat.forEach { a -> AyahBlock(a, highlight = if (a.number == 2) listOf(2) else emptyList(), onWord = { if (a.number == 2 && it == 2) popup = true }) }
    }
}

@Composable
fun WordSheet(onDismiss: () -> Unit, onSarf: () -> Unit) {
    val c = Jawhar.colors
    val t = Jawhar.type
    JBottomSheet(onDismiss) {
        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f)) {
                JText("Lord, Sustainer", t.titleL, c.onSurface)
                JText("rabbi", t.translit, c.onSurfaceVariant)
            }
            JArabic("رَبِّ", t.arabicWordL, c.onSurface)
        }
        JCard(Modifier.fillMaxWidth(), padding = 8.dp) {
            listOf("Root" to "ر ب ب", "Pattern" to "فَعٌّ", "Part of speech" to "Noun · Genitive", "Role in verse" to "Mudaf").forEach { (a, b) ->
                Row(Modifier.fillMaxWidth().padding(horizontal = 12.dp, vertical = 12.dp), verticalAlignment = Alignment.CenterVertically) {
                    JText(a, t.labelM, c.onSurfaceSubtle, Modifier.weight(1f))
                    JText(b, t.titleS, c.onSurface)
                }
            }
        }
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            listOf("Masculine", "Singular", "Genitive").forEach { JTag(it, background = c.primaryContainer, color = c.onPrimaryContainer) }
        }
        TwoButtons("Add to cards", onDismiss, "Open in Sarf", onSarf)
    }
}

@Composable
fun SearchScreen(empty: Boolean = false) {
    val c = Jawhar.colors
    val t = Jawhar.type
    val top = LocalTopInset.current
    var q by remember { mutableStateOf(if (empty) "xyzq" else "rahma") }
    var tab by remember { mutableStateOf(0) }
    val results = listOf(
        Triple("Al-Fatiha 1:1", AyahItem(1, listOf("بِسْمِ", "ٱللَّهِ", "ٱلرَّحْمَٰنِ", "ٱلرَّحِيمِ"), "", "In the name of God, the Most Gracious, the Most Merciful."), listOf(2, 3)),
        Triple("Al-Fatiha 1:3", AyahItem(3, listOf("ٱلرَّحْمَٰنِ", "ٱلرَّحِيمِ"), "", "The Most Gracious, the Most Merciful."), listOf(0, 1)),
        Triple("Ar-Rahman 55:1", AyahItem(1, listOf("ٱلرَّحْمَٰنُ"), "", "The Most Gracious."), listOf(0)),
    )
    Page(
        overlay = {
            Box(Modifier.align(Alignment.TopStart).fillMaxWidth().padding(top = top + 6.dp, start = 72.dp, end = 24.dp)) {
                JSearchField(q, { q = it }, "Search surah, ayah or word")
            }
        },
    ) {
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            listOf("Ayat", "Words", "Roots").forEachIndexed { i, l -> JChip(l, tab == i, { tab = i }) }
        }
        if (empty) {
            Spacer(Modifier.height(40.dp))
            JCenterState(JI.Search, c.bgSurfaceVariant, c.onSurfaceVariant, "No results for \"$q\"", "Check the spelling, or try the root letters instead.")
        } else {
            results.forEach { (ref, ayah, hl) ->
                JCard(Modifier.fillMaxWidth(), padding = 20.dp) {
                    JText(ref, t.labelM, c.onSurfaceSubtle)
                    Spacer(Modifier.height(8.dp))
                    AyahWords(ayah.words, hl, highlightColor = c.accentContainer)
                    Spacer(Modifier.height(8.dp))
                    JText(ayah.english, t.bodyS, c.onSurfaceVariant)
                }
            }
        }
    }
}
