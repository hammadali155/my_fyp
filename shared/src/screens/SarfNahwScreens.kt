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
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.runtime.rememberCoroutineScope
import kotlinx.coroutines.launch
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
import com.meher.jawhar.data.LocalApi
import com.meher.jawhar.data.api.AnalyzeResponseDto
import com.meher.jawhar.data.api.WordFamilyResponseDto
import com.meher.jawhar.data.api.ConjugateResponseDto
import com.meher.jawhar.data.api.NahwParseResponseDto
import com.meher.jawhar.data.api.nahwParse
import com.meher.jawhar.design.*
import com.meher.jawhar.nav.Dest
import com.meher.jawhar.nav.LocalNav
import kotlin.math.PI
import kotlin.math.cos
import kotlin.math.sin

@Composable
fun SarfEngineScreen(timeout: Boolean = false) {
    val nav = LocalNav.current
    val api = LocalApi.current
    val c = Jawhar.colors
    val t = Jawhar.type
    var word by remember { mutableStateOf("يَكْتُبُونَ") }
    var loading by remember { mutableStateOf(false) }
    var failed by remember { mutableStateOf(timeout) }
    var result by remember { mutableStateOf<AnalyzeResponseDto?>(null) }
    var analyse by remember { mutableStateOf(false) }

    if (analyse) {
        LaunchedEffect(word) {
            analyse = false
            loading = true
            failed = false
            result = null
            try {
                result = api.analyze(word)
            } catch (e: Exception) {
                failed = true
            } finally {
                loading = false
            }
        }
    }

    val root = result?.root
    val showResult = result != null

    Page(
        title = "Sarf Engine",
        right = JI.More,
        cta = {
            if (failed) JButton("Back", { nav.back() }, style = JButtonStyle.Neutral)
            else if (showResult) TwoButtons("Word family", { nav.go(Dest.WordFamily) }, "Conjugation", { nav.go(Dest.Conjugation) })
        },
    ) {
        JCard(Modifier.fillMaxWidth(), radius = 30.dp, padding = 20.dp) {
            JText("ARABIC WORD", t.labelS, c.onSurfaceSubtle)
            CompositionLocalProvider(LocalLayoutDirection provides LayoutDirection.Rtl) {
                BasicTextField(word, { word = it; result = null }, Modifier.fillMaxWidth(), textStyle = t.arabicQuranL.copy(color = c.onSurface), cursorBrush = SolidColor(c.primary), singleLine = true)
            }
            JButton("Analyse", { analyse = true }, Modifier.width(112.dp), height = 36.dp, enabled = !loading && word.isNotBlank())
        }
        when {
            loading -> {
                JSkeleton(Modifier.fillMaxWidth().height(120.dp), radius = 34.dp)
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    repeat(2) { JSkeleton(Modifier.weight(1f).height(72.dp), radius = 22.dp) }
                }
            }
            failed -> {
                Column(Modifier.fillMaxWidth().clip(SquircleShape(34.dp)).background(c.errorContainer).padding(24.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    Box(Modifier.size(44.dp).clip(CircleShape).background(c.bgSurface), contentAlignment = Alignment.Center) { JIcon(JI.Clock, size = 22.dp, tint = c.error) }
                    JText("The analyser is taking too long", t.headlineS, c.onSurface)
                    JText("This can happen with long sentences or a slow connection. Your word was not lost.", t.bodyM, c.onSurfaceVariant)
                    JButton("Try again", { analyse = true }, Modifier.width(120.dp), height = 40.dp)
                }
            }
            showResult -> {
                val r = result!!
                HeroCard(color = c.primaryContainer, starColor = c.primary, stars = listOf(StarSpec(330.dp, 20.dp, 220.dp, 0.2f))) {
                    JText("ROOT", t.labelS, c.onPrimaryContainer)
                    CompositionLocalProvider(LocalLayoutDirection provides LayoutDirection.Rtl) {
                        Row(Modifier.fillMaxWidth().padding(vertical = 12.dp), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                            (r.root ?: "—").split(" ").take(3).forEach { l ->
                                Box(Modifier.size(56.dp).clip(CircleShape).background(c.bgSurface), contentAlignment = Alignment.Center) { JArabic(l, t.arabicHeading, c.onPrimaryContainer) }
                            }
                        }
                    }
                    Row(Modifier.fillMaxWidth()) {
                        Column(Modifier.weight(1f)) { JText("Pattern", t.labelM, c.onPrimaryContainer.copy(alpha = 0.8f)); JText(r.pattern ?: "—", t.titleM, c.onSurface) }
                        Column(Modifier.weight(1f)) { JText("Lemma", t.labelM, c.onPrimaryContainer.copy(alpha = 0.8f)); JText(r.lemma ?: "—", t.titleM, c.onSurface) }
                    }
                }
                listOf("POS" to (r.pos_tag ?: "—"), "Source" to (r.source ?: "—"), "In corpus" to if (r.is_quranic == true) "Yes" else "No").chunked(2).forEach { pair ->
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
}

@Composable
fun WordFamilyScreen() {
    val api = LocalApi.current
    val c = Jawhar.colors
    val t = Jawhar.type
    var filter by remember { mutableStateOf(0) }
    var family by remember { mutableStateOf<WordFamilyResponseDto?>(null) }
    var loading by remember { mutableStateOf(true) }

    LaunchedEffect(Unit) {
        try { family = api.wordFamily("كتب") } catch (e: Exception) { } finally { loading = false }
    }

    val groups = family?.groups ?: emptyList()
    val allColors = listOf(c.primaryContainer, c.accentContainer, c.infoContainer, c.successContainer, c.errorContainer)
    val nodes = groups.take(5).mapIndexed { i, g ->
        Triple(g.lemma ?: g.pos_tag ?: "?", allColors[i % allColors.size], -90.0 + i * 72.0)
    }

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
            Box(Modifier.size(104.dp).softShadow(CircleShape, 12.dp, 0.3f).clip(CircleShape).background(c.primary), contentAlignment = Alignment.Center) {
                JArabic(family?.root ?: "ك ت ب", t.arabicHeading, c.onPrimary)
            }
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
        if (loading) {
            repeat(4) { JSkeleton(Modifier.fillMaxWidth().height(52.dp), radius = 26.dp) }
        } else {
            val filtered = when (filter) {
                1 -> groups.filter { it.pos_tag?.startsWith("V") == true }
                2 -> groups.filter { it.pos_tag == "N" || it.pos_tag == "PN" }
                3 -> groups.filter { it.pos_tag?.contains("PART") == true }
                else -> groups
            }
            filtered.forEach { g ->
                Row(Modifier.fillMaxWidth().clip(SquircleShape(26.dp)).background(c.bgSurfaceVariant).padding(horizontal = 20.dp, vertical = 12.dp), verticalAlignment = Alignment.CenterVertically) {
                    Column(Modifier.weight(1f)) {
                        JText(g.lemma ?: "—", t.titleM, c.onSurface)
                        JText("${g.pos_tag ?: "—"} · ${g.count} occurrences", t.bodyS, c.onSurfaceVariant)
                    }
                    if (g.lemma != null) JArabic(g.lemma, t.arabicHeading, c.onSurface)
                }
            }
        }
    }
}

@Composable
fun ConjugationScreen() {
    val api = LocalApi.current
    val c = Jawhar.colors
    val t = Jawhar.type
    var tense by remember { mutableStateOf(0) }
    var voice by remember { mutableStateOf(0) }
    var formIdx by remember { mutableStateOf(0) }
    val formNumber = formIdx + 1
    var conjugation by remember { mutableStateOf<ConjugateResponseDto?>(null) }
    var loading by remember { mutableStateOf(false) }

    LaunchedEffect(formNumber) {
        loading = true
        try { conjugation = api.conjugate("كتب", formNumber) } catch (e: Exception) { } finally { loading = false }
    }

    Page(title = "Conjugation", right = JI.More) {
        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f)) {
                JText("to write", t.titleL, c.onSurface)
                JText("Form $formNumber · Root ك ت ب", t.bodyM, c.onSurfaceVariant)
            }
            JArabic(conjugation?.past ?: "كَتَبَ", t.arabicWordL, c.onSurface)
        }
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) { listOf("Past", "Present", "Command").forEachIndexed { i, l -> JChip(l, tense == i, { tense = i }) } }
        JSegmented(listOf("Active", "Passive"), voice, { voice = it })
        if (loading) {
            repeat(5) { JSkeleton(Modifier.fillMaxWidth().height(52.dp), radius = 18.dp) }
        } else if (conjugation?.supported == false) {
            JInfoCard(conjugation?.unsupported_reason ?: "This root pattern is not yet supported.", "", tone = JTone.Neutral, icon = JI.Info)
        } else {
            Row(Modifier.fillMaxWidth()) {
                Spacer(Modifier.width(58.dp))
                listOf("Singular", "Dual", "Plural").forEach { JText(it, t.labelM, c.onSurfaceSubtle, Modifier.weight(1f), TextAlign.Center) }
            }
            val selected = when (tense) { 1 -> conjugation?.present; 2 -> conjugation?.imperative; else -> conjugation?.past }
            Mock.conjugation.forEachIndexed { r, row ->
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(6.dp), verticalAlignment = Alignment.CenterVertically) {
                    JText(row.label, t.labelM, c.onSurfaceVariant, Modifier.width(52.dp))
                    row.forms.forEachIndexed { cIdx, f ->
                        Box(
                            Modifier.weight(1f).height(52.dp).clip(SquircleShape(18.dp)).background(if (r == 0 && cIdx == 0) c.primaryContainer else c.bgSurfaceVariant),
                            contentAlignment = Alignment.Center,
                        ) {
                            val display = if (r == 0 && cIdx == 0) selected ?: f else f
                            if (display == "—") JText(display, t.bodyM, c.onSurfaceSubtle) else JArabic(display, t.arabicTitle, c.onSurface)
                        }
                    }
                }
            }
        }
        JText("Verb form", t.labelM, c.onSurfaceSubtle)
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) { listOf("I", "II", "III", "IV", "V", "VI").forEachIndexed { i, l -> JChip(l, formIdx == i, { formIdx = i }) } }
    }
}

@Composable
fun NahwInputScreen() {
    val nav = LocalNav.current
    val api = LocalApi.current
    val c = Jawhar.colors
    val t = Jawhar.type
    val scope = rememberCoroutineScope()
    var text by remember { mutableStateOf("ٱلْحَمْدُ لِلَّهِ رَبِّ ٱلْعَٰلَمِينَ") }
    var loading by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf(false) }
    var errorMessage by remember { mutableStateOf("") }

    Page(title = "Nahw Parser", right = JI.More, cta = {
        if (loading) {
            JButton("Parsing…", {}, enabled = false)
        } else {
            JButton("Parse sentence", {
                scope.launch {
                    loading = true
                    error = false
                    try {
                        val result = api.nahwParse(text)
                        nav.go(Dest.NahwResult, result)
                    } catch (e: Exception) {
                        error = true
                        errorMessage = e.message ?: "Parse failed"
                    } finally {
                        loading = false
                    }
                }
            })
        }
    }) {
        if (error) {
            StateScreen(JI.Alert, c.errorContainer, c.error, "Could not parse", errorMessage, "Try again", onPrimary = { error = false }, back = true)
        } else {
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
            if (loading) {
                JSkeleton(Modifier.fillMaxWidth().height(120.dp), radius = 34.dp)
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
}

private fun roleKeyToGrammarRole(roleKey: String?, c: JawharColors): GrammarRole {
    val key = (roleKey ?: "").lowercase()
    return when {
        key.contains("mubtada") -> GrammarRole.Mubtada
        key.contains("khabar") -> GrammarRole.Khabar
        key.contains("na't") || key.contains("nat") -> GrammarRole.Nat
        key.contains("mudaf") -> GrammarRole.Mudaf
        key.contains("fa'il") || key.contains("fail") -> GrammarRole.Faail
        key.contains("maf") -> GrammarRole.Maful
        key.contains("harf") -> GrammarRole.Harf
        else -> GrammarRole.Harf
    }
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun NahwResultScreen() {
    val nav = LocalNav.current
    val c = Jawhar.colors
    val t = Jawhar.type
    val parseResult = nav.currentArg as? NahwParseResponseDto
    val tokens = parseResult?.tokens ?: emptyList()
    val hasError = parseResult == null || tokens.isEmpty()
    var selected by remember { mutableStateOf<Int?>(null) }

    Page(title = "Nahw Parser", right = JI.More, overlay = {
        val s = selected
        if (s != null && s < tokens.size) {
            val tok = tokens[s]
            JBottomSheet(onDismiss = { selected = null }, visible = true) {
                Column(Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(12.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                    JTag(tok.role_key ?: "role", background = roleKeyToGrammarRole(tok.role_key, c).color(c).copy(alpha = 0.14f), color = roleKeyToGrammarRole(tok.role_key, c).color(c), height = 28.dp)
                    JArabic(tok.text_uthmani, t.arabicWordL, c.onSurface)
                    JCard(Modifier.fillMaxWidth(), padding = 16.dp) {
                        val rows = listOf(
                            Pair("Position", tok.position.toString()),
                            Pair("Role (AR)", tok.role_ar ?: "—"),
                            Pair("Role (EN)", tok.role_en),
                            Pair("Dep. type", tok.dep_type ?: "—"),
                            Pair("I'rab", tok.irab ?: "—"),
                            Pair("Head index", tok.head_index?.toString() ?: "—"),
                            Pair("Sentence", tok.sentence_index?.toString() ?: "—"),
                        )
                        rows.forEach { pair ->
                            Row(Modifier.fillMaxWidth().padding(vertical = 6.dp), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.SpaceBetween) {
                                JText(pair.first, t.labelM, c.onSurfaceSubtle)
                                JText(pair.second, t.titleS, c.onSurface)
                            }
                        }
                    }
                    TwoButtons("Ask the tutor", { selected = null; nav.go(Dest.TutorChat) }, "Done", { selected = null })
                }
            }
        }
    }) {
        if (hasError) {
            StateScreen(JI.WifiOff, c.errorContainer, c.error, parseResult?.let { "No annotations" } ?: "No data", "The sentence could not be parsed. Try an example verse.", "Try again", onPrimary = { nav.back() }, back = true)
        } else {
            JTag("${parseResult?.source ?: "corpus"} · ${tokens.size} words", background = c.bgSurfaceVariant, color = c.onSurfaceVariant)
            JCard(Modifier.fillMaxWidth(), radius = 34.dp, padding = 16.dp) {
                CompositionLocalProvider(LocalLayoutDirection provides LayoutDirection.Rtl) {
                    FlowRow(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                        tokens.forEachIndexed { i, tok ->
                            val role = roleKeyToGrammarRole(tok.role_key, c)
                            JWordChip(tok.text_uthmani, role, selected = selected == i, onClick = { selected = i })
                        }
                    }
                }
            }
            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                tokens.forEach { tok ->
                    val role = roleKeyToGrammarRole(tok.role_key, c)
                    JTag(tok.role_key?.capitalize() ?: "Role", background = role.color(c).copy(alpha = 0.14f), color = role.color(c), height = 28.dp)
                }
            }
            if (tokens.isNotEmpty()) {
                JInfoCard("Word detail", "Tap any word above to see its full grammatical breakdown.", tone = JTone.Info, icon = JI.Info)
            }
        }
    }
}
