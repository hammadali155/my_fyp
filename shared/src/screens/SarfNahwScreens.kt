package com.meher.jawhar.screens

import androidx.compose.foundation.Canvas
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
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.PathEffect
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.unit.dp
import com.meher.jawhar.design.*
import com.meher.jawhar.nav.Dest
import com.meher.jawhar.nav.LocalNav
import kotlin.math.PI
import kotlin.math.cos
import kotlin.math.sin

@Composable
fun SarfEngineScreen(timeout: Boolean = false) {
    val nav = LocalNav.current
    val c = Jawhar.colors
    val t = Jawhar.type
    var word by remember { mutableStateOf("يَكْتُبُونَ") }
    Page(
        title = "Sarf Engine",
        right = JI.More,
        cta = {
            if (timeout) JButton("Back", { nav.back() }, style = JButtonStyle.Neutral)
            else TwoButtons("Word family", { nav.go(Dest.WordFamily) }, "Conjugation", { nav.go(Dest.Conjugation) })
        },
    ) {
        JCard(Modifier.fillMaxWidth(), radius = 30.dp, padding = 20.dp) {
            JText("ARABIC WORD", t.labelS, c.onSurfaceSubtle)
            CompositionLocalProvider(LocalLayoutDirection provides LayoutDirection.Rtl) {
                BasicTextField(word, { word = it }, Modifier.fillMaxWidth(), textStyle = t.arabicQuranL.copy(color = c.onSurface), cursorBrush = SolidColor(c.primary), singleLine = true)
            }
            JButton("Analyse", {}, Modifier.width(112.dp), height = 36.dp)
        }
        if (timeout) {
            Column(Modifier.fillMaxWidth().clip(SquircleShape(34.dp)).background(c.errorContainer).padding(24.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Box(Modifier.size(44.dp).clip(CircleShape).background(c.bgSurface), contentAlignment = Alignment.Center) { JIcon(JI.Clock, size = 22.dp, tint = c.error) }
                JText("The analyser is taking too long", t.headlineS, c.onSurface)
                JText("This can happen with long sentences or a slow connection. Your word was not lost.", t.bodyM, c.onSurfaceVariant)
                JButton("Try again", {}, Modifier.width(120.dp), height = 40.dp)
            }
        } else {
            HeroCard(color = c.primaryContainer, starColor = c.primary, stars = listOf(StarSpec(330.dp, 20.dp, 220.dp, 0.2f))) {
                JText("ROOT", t.labelS, c.onPrimaryContainer)
                CompositionLocalProvider(LocalLayoutDirection provides LayoutDirection.Rtl) {
                    Row(Modifier.fillMaxWidth().padding(vertical = 12.dp), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                        listOf("ك", "ت", "ب").forEach { l ->
                            Box(Modifier.size(56.dp).clip(CircleShape).background(c.bgSurface), contentAlignment = Alignment.Center) { JArabic(l, t.arabicHeading, c.onPrimaryContainer) }
                        }
                    }
                }
                Row(Modifier.fillMaxWidth()) {
                    Column(Modifier.weight(1f)) { JText("Pattern", t.labelM, c.onPrimaryContainer.copy(alpha = 0.8f)); JText("يَفْعُلُونَ · Form I", t.titleM, c.onSurface) }
                    Column(Modifier.weight(1f)) { JText("Lemma", t.labelM, c.onPrimaryContainer.copy(alpha = 0.8f)); JText("كَتَبَ · to write", t.titleM, c.onSurface) }
                }
            }
            listOf("Tense" to "Present", "Voice" to "Active", "Person" to "Third", "Number" to "Plural", "Gender" to "Masculine", "Mood" to "Indicative").chunked(2).forEach { pair ->
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    pair.forEach { (a, b) ->
                        Column(Modifier.weight(1f).clip(SquircleShape(22.dp)).background(c.bgSurfaceVariant).padding(16.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                            JText(a, t.labelM, c.onSurfaceSubtle)
                            JText(b, t.titleM, c.onSurface)
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun WordFamilyScreen() {
    val c = Jawhar.colors
    val t = Jawhar.type
    var filter by remember { mutableStateOf(0) }
    val nodes = listOf(Triple("كَتَبَ", c.primaryContainer, -90.0), Triple("كِتَابٌ", c.accentContainer, -18.0), Triple("كَاتِبٌ", c.infoContainer, 54.0), Triple("مَكْتُوبٌ", c.infoContainer, 126.0), Triple("مَكْتَبَةٌ", c.accentContainer, 198.0))
    Page(title = "Word family", right = JI.More) {
        Box(Modifier.fillMaxWidth().height(300.dp), contentAlignment = Alignment.Center) {
            Canvas(Modifier.size(300.dp)) {
                val r = 112.dp.toPx()
                val ctr = Offset(size.width / 2f, size.height / 2f)
                drawCircle(c.outline, radius = r, center = ctr, style = Stroke(2.dp.toPx(), cap = StrokeCap.Round, pathEffect = PathEffect.dashPathEffect(floatArrayOf(2f, 16f))))
                nodes.forEach { n ->
                    val a = n.third * PI / 180.0
                    drawLine(c.outline, ctr, Offset(ctr.x + (r * cos(a)).toFloat(), ctr.y + (r * sin(a)).toFloat()), strokeWidth = 1.5.dp.toPx())
                }
            }
            Box(Modifier.size(104.dp).softShadow(CircleShape, 12.dp, 0.3f).clip(CircleShape).background(c.primary), contentAlignment = Alignment.Center) { JArabic("ك ت ب", t.arabicHeading, c.onPrimary) }
            nodes.forEach { n ->
                val a = n.third * PI / 180.0
                Box(Modifier.offset(x = (112 * cos(a)).dp, y = (112 * sin(a)).dp).size(76.dp).clip(CircleShape).background(n.second), contentAlignment = Alignment.Center) {
                    JArabic(n.first, t.arabicTitle, c.onSurface)
                }
            }
        }
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            listOf("All", "Verbs", "Nouns", "Participles").forEachIndexed { i, l -> JChip(l, filter == i, { filter = i }) }
        }
        listOf(Triple("كَتَبَ", "to write", "Verb · Form I"), Triple("كِتَابٌ", "book", "Noun"), Triple("كَاتِبٌ", "writer", "Active participle"), Triple("مَكْتُوبٌ", "written", "Passive participle")).forEach { (ar, en, kind) ->
            Row(Modifier.fillMaxWidth().clip(SquircleShape(26.dp)).background(c.bgSurfaceVariant).padding(horizontal = 20.dp, vertical = 12.dp), verticalAlignment = Alignment.CenterVertically) {
                Column(Modifier.weight(1f)) { JText(en, t.titleM, c.onSurface); JText(kind, t.bodyS, c.onSurfaceVariant) }
                JArabic(ar, t.arabicHeading, c.onSurface)
            }
        }
    }
}

@Composable
fun ConjugationScreen() {
    val c = Jawhar.colors
    val t = Jawhar.type
    var tense by remember { mutableStateOf(0) }
    var voice by remember { mutableStateOf(0) }
    var form by remember { mutableStateOf(0) }
    Page(title = "Conjugation", right = JI.More) {
        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f)) {
                JText("to write", t.titleL, c.onSurface)
                JText("Form I · Root ك ت ب", t.bodyM, c.onSurfaceVariant)
            }
            JArabic("كَتَبَ", t.arabicWordL, c.onSurface)
        }
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) { listOf("Past", "Present", "Command").forEachIndexed { i, l -> JChip(l, tense == i, { tense = i }) } }
        JSegmented(listOf("Active", "Passive"), voice, { voice = it })
        Row(Modifier.fillMaxWidth()) {
            Spacer(Modifier.width(58.dp))
            listOf("Singular", "Dual", "Plural").forEach { JText(it, t.labelM, c.onSurfaceSubtle, Modifier.weight(1f), TextAlign.Center) }
        }
        Mock.conjugation.forEachIndexed { r, row ->
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(6.dp), verticalAlignment = Alignment.CenterVertically) {
                JText(row.label, t.labelM, c.onSurfaceVariant, Modifier.width(52.dp))
                row.forms.forEachIndexed { cIdx, f ->
                    Box(
                        Modifier.weight(1f).height(52.dp).clip(SquircleShape(18.dp)).background(if (r == 0 && cIdx == 0) c.primaryContainer else c.bgSurfaceVariant),
                        contentAlignment = Alignment.Center,
                    ) { if (f == "—") JText(f, t.bodyM, c.onSurfaceSubtle) else JArabic(f, t.arabicTitle, c.onSurface) }
                }
            }
        }
        JText("Verb form", t.labelM, c.onSurfaceSubtle)
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) { listOf("I", "II", "III", "IV", "V", "VI").forEachIndexed { i, l -> JChip(l, form == i, { form = i }) } }
    }
}

@Composable
fun NahwInputScreen() {
    val nav = LocalNav.current
    val c = Jawhar.colors
    val t = Jawhar.type
    var text by remember { mutableStateOf("ٱلْحَمْدُ لِلَّهِ رَبِّ ٱلْعَٰلَمِينَ") }
    Page(title = "Nahw Parser", right = JI.More, cta = { JButton("Parse sentence", { nav.go(Dest.NahwResult) }) }) {
        JCard(Modifier.fillMaxWidth(), radius = 34.dp, padding = 20.dp) {
            JText("ARABIC SENTENCE", t.labelS, c.onSurfaceSubtle)
            CompositionLocalProvider(LocalLayoutDirection provides LayoutDirection.Rtl) {
                BasicTextField(text, { text = it }, Modifier.fillMaxWidth().padding(vertical = 8.dp), textStyle = t.arabicQuranL.copy(color = c.onSurface), cursorBrush = SolidColor(c.primary))
            }
            Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                JText("${text.length} / 200", t.bodyS, c.onSurfaceSubtle, Modifier.weight(1f))
                Box(Modifier.size(28.dp).clip(CircleShape).background(c.bgSurfaceHigh).tappable { text = "" }, contentAlignment = Alignment.Center) { JIcon(JI.Close, size = 14.dp, tint = c.onSurfaceVariant, strokeWidth = 2.dp) }
            }
        }
        SectionTitle("Try an example")
        Mock.examples.forEach { ex ->
            Row(Modifier.fillMaxWidth().clip(SquircleShape(26.dp)).background(c.bgSurfaceVariant).tappable { text = ex.arabic }.padding(horizontal = 20.dp, vertical = 14.dp), verticalAlignment = Alignment.CenterVertically) {
                JText(ex.ref, t.labelM, c.onSurfaceSubtle, Modifier.weight(1f))
                JArabic(ex.arabic, t.arabicQuranM, c.onSurface)
            }
        }
        SectionTitle("Recent")
        Row(Modifier.fillMaxWidth().clip(SquircleShape(26.dp)).background(c.bgSurfaceVariant).padding(horizontal = 20.dp, vertical = 14.dp), verticalAlignment = Alignment.CenterVertically) {
            JText("Yesterday", t.labelM, c.onSurfaceSubtle, Modifier.weight(1f))
            JArabic("إِنَّ ٱللَّهَ غَفُورٌ رَّحِيمٌ", t.arabicTitle, c.onSurface)
        }
    }
}

private class WordInfo(val word: String, val role: GrammarRole, val roleName: String, val note: String, val case: String, val reason: String, val pair: String)

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun NahwResultScreen() {
    val nav = LocalNav.current
    val c = Jawhar.colors
    val t = Jawhar.type
    val words = listOf(
        WordInfo("ٱلْحَمْدُ", GrammarRole.Mubtada, "Mubtada", "Topic of the sentence", "Marfu' (nominative)", "Starts a nominal sentence", "لِلَّهِ · Khabar"),
        WordInfo("لِلَّهِ", GrammarRole.Khabar, "Khabar", "Completes the topic", "Majrur (genitive)", "Follows the preposition lam", "ٱلْحَمْدُ · Mubtada"),
        WordInfo("رَبِّ", GrammarRole.Nat, "Na't", "Describes ٱللَّه", "Majrur (genitive)", "Follows the word it describes", "لِلَّهِ"),
        WordInfo("ٱلْعَٰلَمِينَ", GrammarRole.Mudaf, "Mudaf ilayh", "Possessor of رَبِّ", "Majrur (genitive)", "Second part of an idafa", "رَبِّ"),
    )
    var selected by remember { mutableStateOf<Int?>(0) }
    Page(title = "Nahw Parser", right = JI.More, overlay = {
        val s = selected
        if (s != null) {
            val w = words[s]
            JBottomSheet(onDismiss = { selected = null }) {
                Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                    Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                        JTag(w.roleName, background = w.role.color(c).copy(alpha = 0.14f), color = w.role.color(c), height = 28.dp)
                        JText(w.note, t.bodyS, c.onSurfaceVariant)
                    }
                    JArabic(w.word, t.arabicWordL, c.onSurface)
                }
                JCard(Modifier.fillMaxWidth(), padding = 8.dp) {
                    listOf("Case" to w.case, "Reason" to w.reason, "Pairs with" to w.pair).forEach { (a, b) ->
                        Row(Modifier.fillMaxWidth().padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
                            JText(a, t.labelM, c.onSurfaceSubtle, Modifier.weight(1f))
                            JText(b, t.titleS, c.onSurface)
                        }
                    }
                }
                TwoButtons("Ask the tutor", { selected = null; nav.go(Dest.TutorChat) }, "Add to cards", { selected = null })
            }
        }
    }) {
        JTag("Al-Fatiha · 1:2", background = c.bgSurfaceVariant, color = c.onSurfaceVariant)
        JCard(Modifier.fillMaxWidth(), radius = 34.dp, padding = 16.dp) {
            CompositionLocalProvider(LocalLayoutDirection provides LayoutDirection.Rtl) {
                FlowRow(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    words.forEachIndexed { i, w -> JWordChip(w.word, w.role, selected = selected == i, onClick = { selected = i }) }
                }
            }
        }
        FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            words.forEach { JTag(it.roleName, background = it.role.color(c).copy(alpha = 0.14f), color = it.role.color(c), height = 28.dp) }
        }
    }
}
