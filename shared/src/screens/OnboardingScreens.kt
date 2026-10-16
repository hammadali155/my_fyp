package com.meher.jawhar.screens

import androidx.compose.foundation.ExperimentalFoundationApi
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
fun PlacementScreen() {
    val nav = LocalNav.current
    val qs = Mock.placementQuestions
    var step by remember { mutableStateOf(0) }
    var picks by remember { mutableStateOf(List<Int?>(qs.size) { null }) }

    val pick: (Int) -> Unit = { i ->
        picks = picks.toMutableList().also { it[step - 1] = i }
    }

    when {
        step == 0 -> PlacementIntroStep(questions = qs.size, onStart = { step = 1 })
        step > qs.size -> PlacementResultStep(
            picks = picks,
            onBack = { step = qs.size },
            onBuild = { nav.go(Dest.DailyGoal) },
        )
        else -> {
            val i = step - 1
            PlacementQuestionStep(
                q = qs[i],
                index = i,
                total = qs.size,
                picked = picks[i],
                onPick = pick,
                onBack = { step -= 1 },
                onNext = { step += 1 },
            )
        }
    }
}

@Composable
internal fun PlacementIntroStep(questions: Int, onStart: () -> Unit) {
    val nav = LocalNav.current
    val c = Jawhar.colors
    Page(
        cta = {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                JButton("Start assessment", onStart)
                JButton("Skip, start from the beginning", { nav.reset(Dest.Home) }, style = JButtonStyle.Text)
            }
        },
    ) {
        Box(
            Modifier.fillMaxWidth().height(160.dp).clip(SquircleShape(48.dp)).background(c.primaryContainer)
                .starOrnaments(c.primary, StarSpec(80.dp, 60.dp, 260.dp, 0.3f), StarSpec(320.dp, 20.dp, 200.dp, 0.22f)),
            contentAlignment = Alignment.Center,
        ) {
            Row(horizontalArrangement = Arrangement.spacedBy(20.dp)) {
                listOf(JI.Cards, JI.Tree, JI.Layers).forEach { ic ->
                    Box(Modifier.size(72.dp).clip(CircleShape).background(c.bgSurface), contentAlignment = Alignment.Center) {
                        JIcon(ic, size = 32.dp, tint = c.primary)
                    }
                }
            }
        }
        BigTitle("Find your starting point", "It takes about 6 minutes and sets your level in three areas.")
        JListItem("Vocabulary", subtitle = "Words you already know", icon = JI.Cards, trailing = null)
        JListItem("Sarf", subtitle = "How words are built from roots", icon = JI.Tree, trailing = null)
        JListItem("Nahw", subtitle = "How words connect in a sentence", icon = JI.Layers, trailing = null)
        JText("$questions questions · about 6 minutes", Jawhar.type.labelM, c.onSurfaceSubtle, Modifier.fillMaxWidth(), TextAlign.Center)
    }
}

@Composable
internal fun PlacementQuestionStep(
    q: PlacementQ,
    index: Int,
    total: Int,
    picked: Int?,
    onPick: (Int) -> Unit,
    onBack: () -> Unit,
    onNext: () -> Unit,
) {
    val c = Jawhar.colors
    Page(
        backIcon = JI.Back,
        onBack = onBack,
        overlay = { TopProgress((index + 1).toFloat() / total, "${index + 1} / $total") },
        cta = { JButton(if (index + 1 == total) "See my level" else "Next", onNext, enabled = picked != null) },
    ) {
        JTag("${q.skill}", background = c.primaryContainer, color = c.onPrimaryContainer)
        JText(q.prompt, Jawhar.type.headlineM, c.onSurface)
        if (q.word != null) {
            Box(
                Modifier.fillMaxWidth().height(148.dp).clip(SquircleShape(34.dp)).background(c.bgSurfaceVariant)
                    .starOrnaments(c.primary, StarSpec(171.dp, 74.dp, 220.dp, 0.14f)),
                contentAlignment = Alignment.Center,
            ) { JArabic(q.word, Jawhar.type.arabicWordXL, c.onSurface) }
        }
        q.options.forEachIndexed { i, o ->
            JQuizOption(o, listOf("A", "B", "C", "D")[i], if (picked == i) JQuizState.Selected else JQuizState.Default, { onPick(i) }, arabic = true)
        }
    }
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
internal fun PlacementResultStep(picks: List<Int?>, onBack: () -> Unit, onBuild: () -> Unit) {
    val c = Jawhar.colors
    val t = Jawhar.type
    val score = Mock.placementScore(picks)
    val overall = score.values.average().toFloat()
    val level = when {
        overall >= 0.85f -> "Advanced"
        overall >= 0.6f -> "Intermediate"
        overall >= 0.3f -> "Beginner II"
        else -> "Beginner I"
    }
    val focus = score.entries.sortedBy { it.value }.filter { it.value < overall }.take(2)

    Page(back = false, cta = { JButton("Build my learning path", onBuild) }) {
        HeroCard(stars = listOf(StarSpec(330.dp, 20.dp, 240.dp, 0.28f), StarSpec(300.dp, 150.dp, 160.dp, 0.2f))) {
            JText("YOUR STARTING LEVEL", t.labelS, c.accent)
            JText(level, t.headlineL, c.onPrimary)
            Spacer(Modifier.height(8.dp))
            JText("${(overall * 100).toInt()}% overall. We will start here and build up from there.", t.bodyM, c.onPrimary.copy(alpha = 0.82f), Modifier.padding(end = 70.dp))
        }
        SectionTitle("Your three skills")
        listOf(Triple("Vocabulary", score["Vocabulary"], JI.Cards), Triple("Sarf", score["Sarf"], JI.Tree), Triple("Nahw", score["Nahw"], JI.Layers)).forEach { (label, v, ic) ->
            JCard(Modifier.fillMaxWidth(), radius = 26.dp) {
                Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    JIcon(ic, size = 20.dp, tint = c.primary)
                    JText(label, t.titleS, c.onSurface, Modifier.weight(1f))
                    JText("${((v ?: 0f) * 100).toInt()}%", t.labelL, c.onSurfaceVariant)
                }
                Spacer(Modifier.height(12.dp))
                JProgressBar(v ?: 0f, track = c.bgSurfaceHigh)
            }
        }
        SectionTitle("Focus areas", "Review answers") { onBack() }
        FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            if (focus.isEmpty()) {
                JChip("Full syllabus ahead", false, {})
            } else {
                focus.forEach { (skill, v) -> JChip("$skill · ${(v * 100).toInt()}%", false, {}) }
            }
        }
    }
}

@Composable
fun DailyGoalScreen() {
    val nav = LocalNav.current
    val c = Jawhar.colors
    var picked by remember { mutableStateOf(1) }
    val goals = listOf(Triple("5", "Casual", "A few cards a day"), Triple("10", "Regular", "Steady, one short lesson"), Triple("15", "Serious", "A lesson and a review"), Triple("25", "Intense", "Fastest progress"))
    Page(cta = { JButton("Continue", { nav.go(Dest.NotifPermission) }) }) {
        BigTitle("Set a daily goal", "How much time can you give Arabic each day?")
        goals.forEachIndexed { i, (m, t, sub) ->
            val on = picked == i
            Row(
                Modifier.fillMaxWidth().clip(SquircleShape(28.dp)).background(if (on) c.primaryContainer else c.bgSurfaceVariant).tappable { picked = i }.padding(horizontal = 20.dp, vertical = 14.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(20.dp),
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    JText(m, Jawhar.type.headlineM, if (on) c.onPrimaryContainer else c.onSurface)
                    JText("min", Jawhar.type.labelM, c.onSurfaceVariant)
                }
                Column(Modifier.weight(1f)) {
                    JText(t, Jawhar.type.titleM, c.onSurface)
                    JText(sub, Jawhar.type.bodyS, c.onSurfaceVariant)
                }
                Box(Modifier.size(28.dp).clip(CircleShape).background(if (on) c.primary else c.bgSurfaceHigh), contentAlignment = Alignment.Center) {
                    if (on) JIcon(JI.Check, size = 16.dp, tint = c.onPrimary, strokeWidth = 2.2.dp)
                }
            }
        }
        JText("You can change this anytime in Settings", Jawhar.type.bodyM, c.onSurfaceSubtle, Modifier.fillMaxWidth(), TextAlign.Center)
    }
}

@Composable
fun NotificationPermissionScreen() {
    val nav = LocalNav.current
    val c = Jawhar.colors
    Page(
        back = false,
        cta = {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                JButton("Allow notifications", { nav.reset(Dest.Home) })
                JButton("Not now", { nav.reset(Dest.Home) }, style = JButtonStyle.Text)
            }
        },
    ) {
        Box(Modifier.fillMaxWidth().padding(top = 40.dp), contentAlignment = Alignment.Center) {
            Box(Modifier.size(300.dp).starOrnaments(c.accent, StarSpec(150.dp, 150.dp, 300.dp, 0.3f)), contentAlignment = Alignment.Center) {
                Box(Modifier.size(184.dp).clip(CircleShape).background(c.primaryContainer), contentAlignment = Alignment.Center) {
                    JIcon(JI.Bell, size = 80.dp, tint = c.primary, strokeWidth = 1.6.dp)
                }
            }
        }
        BigTitle("Gentle reminders", "A short nudge each day keeps your streak alive. No spam, ever.", center = true)
        JListItem("Remind me at", icon = JI.Clock, trailing = {
            JText("8:00 PM", Jawhar.type.labelL, c.onSurfaceVariant)
            JIcon(JI.Chevron, size = 20.dp, tint = c.onSurfaceSubtle)
        })
    }
}
