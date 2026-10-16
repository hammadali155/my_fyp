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
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.PathEffect
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.meher.jawhar.data.LocalApi
import com.meher.jawhar.data.api.me
import com.meher.jawhar.data.api.srsDue
import com.meher.jawhar.design.*
import com.meher.jawhar.nav.Dest
import com.meher.jawhar.nav.LocalNav

@Composable
fun HomeScreen() {
    val nav = LocalNav.current
    val api = LocalApi.current
    val c = Jawhar.colors
    val t = Jawhar.type
    val top = LocalTopInset.current
    var userName by remember { mutableStateOf("there") }
    var streak by remember { mutableStateOf(0) }
    var xp by remember { mutableStateOf(0) }
    var dueCount by remember { mutableStateOf(0) }
    var newCount by remember { mutableStateOf(0) }

    LaunchedEffect(Unit) {
        try {
            val user = api.me()
            userName = user.name.split(" ").first()
            streak = user.streak_days
            xp = user.xp
        } catch (e: Exception) { }
        try {
            val due = api.srsDue()
            dueCount = due.size
            newCount = due.count { it.new_card }
        } catch (e: Exception) { }
    }

    Page(
        back = false,
        tab = JTab.Home,
        right = JI.Bell,
        overlay = {
            val shape = CapsuleShape
            Row(
                Modifier.align(Alignment.TopStart).padding(top = top + 8.dp, start = 16.dp).height(48.dp).softShadow(shape, 14.dp, 0.3f).clip(shape).background(c.bgSurface.copy(alpha = 0.92f)).padding(horizontal = 16.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                JIcon(JI.Flame, size = 22.dp, tint = c.onAccentContainer)
                JText("$streak days", t.labelL, c.onSurface)
            }
        },
    ) {
        Column {
            JText("As-salamu alaykum,", t.bodyL, c.onSurfaceVariant)
            JText(userName, t.headlineL, c.onSurface)
        }
        HeroCard(Modifier.fillMaxWidth(), stars = listOf(StarSpec(330.dp, 20.dp, 250.dp, 0.26f), StarSpec(300.dp, 190.dp, 170.dp, 0.18f))) {
            JText("TODAY'S REVIEW", t.labelS, c.accent)
            JText("$dueCount cards to review today", t.headlineM, c.onPrimary, Modifier.padding(top = 4.dp, end = 80.dp))
            JText("$newCount new words in queue", t.bodyM, c.onPrimary.copy(alpha = 0.82f), Modifier.padding(top = 8.dp))
            JButton("Start session", { nav.go(Dest.FlashFront) }, Modifier.padding(top = 16.dp).width(150.dp), JButtonStyle.Accent, height = 44.dp)
        }
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(9.dp)) {
            JStatTile(JI.Flame, streak.toString(), "Day streak", c.accentContainer, c.onAccentContainer, Modifier.weight(1f))
            JStatTile(JI.Bolt, xp.toString(), "Total XP", c.primaryContainer, c.onPrimaryContainer, Modifier.weight(1f))
            JStatTile(JI.Cards, dueCount.toString(), "Due today", c.infoContainer, c.info, Modifier.weight(1f))
        }
        Row(
            Modifier.fillMaxWidth().clip(SquircleShape(30.dp)).background(c.bgSurfaceVariant).tappable { nav.go(Dest.Lesson) }.padding(20.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            Box(Modifier.size(56.dp).clip(CircleShape).background(c.accent), contentAlignment = Alignment.Center) { JIcon(JI.Play, size = 28.dp, tint = c.onAccent, filled = true) }
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                JText("CONTINUE LEARNING", t.labelS, c.onSurfaceSubtle)
                JText("Sarf · Form I verbs", t.titleM, c.onSurface)
                Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    JProgressBar(0.75f, Modifier.weight(1f), height = 6.dp)
                    JText("75%", t.labelM, c.onSurfaceVariant)
                }
            }
        }
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(9.dp)) {
            listOf(Triple("Sarf Engine", JI.Tree, Dest.Sarf), Triple("Nahw Parser", JI.Layers, Dest.NahwInput), Triple("Vocabulary", JI.Cards, Dest.Vocab)).forEach { (label, ic, dest) ->
                Column(
                    Modifier.weight(1f).clip(SquircleShape(26.dp)).background(c.bgSurfaceVariant).tappable { nav.go(dest) }.padding(14.dp),
                    verticalArrangement = Arrangement.spacedBy(14.dp),
                ) {
                    Box(Modifier.size(40.dp).clip(CircleShape).background(c.primaryContainer), contentAlignment = Alignment.Center) { JIcon(ic, size = 22.dp, tint = c.onPrimaryContainer) }
                    JText(label, t.titleS, c.onSurface)
                }
            }
        }
        Column(
            Modifier.fillMaxWidth().clip(SquircleShape(30.dp)).background(c.accentContainer).tappable { nav.go(Dest.DailyChallenge) }.padding(20.dp),
            verticalArrangement = Arrangement.spacedBy(6.dp),
        ) {
            JText("DAILY CHALLENGE", t.labelS, c.onAccentContainer)
            JText("Analyse 3 verbs from Surah Al-Fatiha", t.titleM, c.onSurface)
            JText("+50 XP", t.labelL, c.onAccentContainer)
        }
    }
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun LearnPathScreen() {
    val nav = LocalNav.current
    val c = Jawhar.colors
    val t = Jawhar.type
    var filter by remember { mutableStateOf(2) }
    val nodes = listOf(Triple("Past tense", JNodeState.Completed, 0), Triple("Present tense", JNodeState.Completed, -60), Triple("Command form", JNodeState.Current, 60), Triple("Form II", JNodeState.Locked, -55))
    Page(back = false, tab = JTab.Learn, right = JI.Sliders) {
        JText("Your path", t.headlineL, c.onSurface)
        FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            listOf("All", "Vocabulary", "Sarf", "Nahw").forEachIndexed { i, l -> JChip(l, filter == i, { filter = i }) }
        }
        Row(Modifier.fillMaxWidth().clip(SquircleShape(24.dp)).background(c.accentContainer).padding(horizontal = 20.dp, vertical = 14.dp), verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f)) {
                JText("UNIT 2 · VERB FORMS", t.labelS, c.onAccentContainer)
                JText("Form I, past and present", t.titleS, c.onSurface)
            }
            JText("3 of 4", t.labelL, c.onAccentContainer)
        }
        Column(
            Modifier.fillMaxWidth().drawBehind {
                val cx = size.width / 2f
                val step = 108.dp.toPx()
                for (i in 0 until nodes.size - 1) {
                    val x1 = cx + nodes[i].third.dp.toPx()
                    val x2 = cx + nodes[i + 1].third.dp.toPx()
                    val y1 = i * step + 72.dp.toPx()
                    val y2 = (i + 1) * step + 36.dp.toPx()
                    drawLine(c.outline, Offset(x1, y1), Offset(x2, y2), strokeWidth = 3.dp.toPx(), cap = StrokeCap.Round, pathEffect = PathEffect.dashPathEffect(floatArrayOf(2f, 18f)))
                }
            },
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            nodes.forEach { (label, state, dx) ->
                Box(Modifier.fillMaxWidth(), contentAlignment = Alignment.TopCenter) {
                    JLessonNode(label, state, Modifier.offset(x = dx.dp), onClick = { if (state != JNodeState.Locked) nav.go(Dest.Lesson) })
                }
            }
        }
    }
}

@Composable
fun LessonScreen() {
    val nav = LocalNav.current
    val lesson = Mock.lessonFormI
    var step by remember { mutableStateOf(0) }
    var picks by remember { mutableStateOf(List<Int?>(lesson.quiz.size) { null }) }

    val contentEnd = lesson.steps.size
    val doneStep = contentEnd + lesson.quiz.size + 1
    val pick: (Int) -> Unit = { i -> picks = picks.toMutableList().also { it[step - contentEnd - 1] = i } }
    val back: () -> Unit = { if (step == 0) nav.back() else step -= 1 }

    when {
        step == 0 -> LessonIntroStep(lesson, onStart = { step = 1 })
        step == doneStep -> LessonCompleteStep(
            lesson = lesson,
            accuracy = Mock.lessonScore(lesson.quiz, picks),
            onBack = { step = contentEnd },
            onContinue = { nav.reset(Dest.Home) },
            onReview = { nav.go(Dest.FlashFront) },
        )
        step > contentEnd -> {
            val i = step - contentEnd - 1
            LessonQuizStep(
                q = lesson.quiz[i],
                index = i,
                total = lesson.quiz.size,
                picked = picks[i],
                onPick = pick,
                onBack = back,
                onNext = { step += 1 },
            )
        }
        else -> LessonContentStep(
            step = lesson.steps[step - 1],
            index = step - 1,
            total = contentEnd,
            onNext = { step += 1 },
        )
    }
}

@Composable
internal fun LessonIntroStep(lesson: Lesson, onStart: () -> Unit) {
    val nav = LocalNav.current
    val c = Jawhar.colors
    val t = Jawhar.type
    Page(right = JI.Bookmark, cta = { JButton("Start lesson", onStart) }) {
        Box(
            Modifier.fillMaxWidth().height(230.dp).clip(SquircleShape(48.dp)).background(c.accentContainer)
                .starOrnaments(c.accent, StarSpec(80.dp, 40.dp, 260.dp, 0.35f), StarSpec(320.dp, 220.dp, 200.dp, 0.28f)),
            contentAlignment = Alignment.Center,
        ) {
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                JArabic(lesson.pattern, t.arabicWordXL, c.onAccentContainer)
                JTag(lesson.form)
            }
        }
        BigTitle(lesson.title, lesson.subtitle)
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            JTag("${lesson.minutes} min", background = c.bgSurfaceVariant, color = c.onSurfaceVariant, icon = JI.Clock)
            JTag("${lesson.wordCount} words", background = c.bgSurfaceVariant, color = c.onSurfaceVariant, icon = JI.Cards)
            JTag("${lesson.quiz.size} questions", background = c.bgSurfaceVariant, color = c.onSurfaceVariant, icon = JI.Help)
        }
        SectionTitle("You will learn")
        listOf(lesson.goals).flatten().forEach {
            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                Box(Modifier.size(22.dp).clip(CircleShape).background(c.primaryContainer), contentAlignment = Alignment.Center) { JIcon(JI.Check, size = 12.dp, tint = c.onPrimaryContainer, strokeWidth = 2.4.dp) }
                JText(it, t.bodyM, c.onSurface)
            }
        }
    }
}

@Composable
internal fun LessonContentStep(step: LessonStep, index: Int, total: Int, onNext: () -> Unit) {
    val c = Jawhar.colors
    val t = Jawhar.type
    Page(backIcon = JI.Close, overlay = { TopProgress((index + 1).toFloat() / total, "${index + 1} / $total") }, cta = { JButton("Continue", onNext) }) {
        Column {
            JText(step.kicker, t.labelS, c.primary)
            JText(step.title, t.headlineM, c.onSurface)
        }
        Column(
            Modifier.fillMaxWidth().clip(SquircleShape(34.dp)).background(c.bgSurfaceVariant).padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            JArabic(step.word ?: "", t.arabicWordL, c.onSurface)
            JText(step.translit ?: "", t.translit, c.onSurfaceVariant)
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.padding(top = 8.dp)) {
                step.tags.forEach { JTag(it) }
            }
        }
        JText(step.body, t.bodyL, c.onSurface)
        JInfoCard("Tip", "Tap any Arabic word in a lesson to see its root, pattern and meaning.", tone = JTone.Accent)
    }
}

@Composable
internal fun LessonQuizStep(q: LessonQ, index: Int, total: Int, picked: Int?, onPick: (Int) -> Unit, onBack: () -> Unit, onNext: () -> Unit) {
    val c = Jawhar.colors
    val t = Jawhar.type
    Page(
        backIcon = JI.Close,
        onBack = onBack,
        overlay = { TopProgress((index + 1).toFloat() / total, "${index + 1} / $total") },
        cta = {
            if (picked == null) {
                JButton("Check", {}, enabled = false)
            } else {
                val ok = picked == q.answer
                Column(
                    Modifier.fillMaxWidth().clip(SquircleShape(34.dp)).background(if (ok) c.successContainer else c.errorContainer).padding(20.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp),
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                        JIcon(if (ok) JI.Check else JI.Close, size = 22.dp, tint = if (ok) c.success else c.error, strokeWidth = 2.2.dp)
                        JText(if (ok) "Correct" else "Not quite", t.titleL, if (ok) c.success else c.error)
                    }
                    JText(q.explain, t.bodyM, c.onSurface)
                    JButton("Continue", onNext)
                }
            }
        },
    ) {
        JText(q.prompt, t.headlineM, c.onSurface)
        q.options.forEachIndexed { i, o ->
            val s = when {
                picked == null -> JQuizState.Default
                i == q.answer -> JQuizState.Correct
                i == picked -> JQuizState.Incorrect
                else -> JQuizState.Default
            }
            JQuizOption(o, listOf("A", "B", "C", "D")[i], s, { if (picked == null) onPick(i) }, arabic = true)
        }
    }
}

@Composable
internal fun LessonCompleteStep(lesson: Lesson, accuracy: Float, onBack: () -> Unit, onContinue: () -> Unit, onReview: () -> Unit) {
    val c = Jawhar.colors
    val t = Jawhar.type
    Page(
        back = false,
        cta = {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                JButton("Continue", onContinue)
                JButton("Review mistakes", onReview, style = JButtonStyle.Neutral)
            }
        },
    ) {
        Box(Modifier.fillMaxWidth().padding(top = 24.dp), contentAlignment = Alignment.Center) {
            Box(Modifier.size(330.dp).starOrnaments(c.accent, StarSpec(165.dp, 165.dp, 330.dp, 0.3f), StarSpec(165.dp, 165.dp, 230.dp, 0.4f)), contentAlignment = Alignment.Center) {
                Box(Modifier.size(152.dp).softShadow(CircleShape, 12.dp, 0.3f).clip(CircleShape).background(c.accent), contentAlignment = Alignment.Center) {
                    JIcon(JI.Trophy, size = 68.dp, tint = c.onAccent, strokeWidth = 1.6.dp)
                }
            }
        }
        BigTitle("Lesson complete", lesson.title, center = true)
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.Center) { JTag("+${lesson.xp} XP", background = c.accentContainer, color = c.onAccentContainer, height = 36.dp) }
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(9.dp)) {
            JStatTile(JI.Target, "${(accuracy * 100).toInt()}%", "Accuracy", c.primaryContainer, c.onPrimaryContainer, Modifier.weight(1f))
            JStatTile(JI.Help, lesson.quiz.size.toString(), "Questions", c.accentContainer, c.onAccentContainer, Modifier.weight(1f))
            JStatTile(JI.Clock, "${lesson.minutes}", "Minutes", c.infoContainer, c.info, Modifier.weight(1f))
        }
    }
}

@Composable
fun DailyChallengeScreen() {
    val c = Jawhar.colors
    val t = Jawhar.type
    val nav = LocalNav.current
    Page {
        BigTitle("Daily challenge")
        JTag("Resets in 6h 12m", background = c.accentContainer, color = c.onAccentContainer, icon = JI.Clock, height = 36.dp)
        HeroCard(color = c.accentContainer, starColor = c.accent, stars = listOf(StarSpec(330.dp, 20.dp, 220.dp, 0.3f))) {
            JText("TODAY", t.labelS, c.onAccentContainer)
            JText("Parse the ayah", t.headlineM, c.onSurface)
            JText("Analyse the four words of Al-Fatiha 1:2 and tag each grammatical role.", t.bodyM, c.onSurfaceVariant, Modifier.padding(top = 8.dp))
            Row(Modifier.fillMaxWidth().padding(top = 16.dp), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                JProgressBar(0.25f, Modifier.weight(1f), track = c.bgSurface, fill = c.onAccentContainer)
                JText("1 of 4 words", t.labelM, c.onAccentContainer)
            }
            Row(Modifier.fillMaxWidth().padding(top = 16.dp), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.SpaceBetween) {
                JButton("Continue", { nav.go(Dest.NahwResult) }, Modifier.width(120.dp), JButtonStyle.Accent, height = 36.dp)
                JTag("+50 XP", background = c.bgSurface, color = c.onAccentContainer, height = 36.dp)
            }
        }
        SectionTitle("More challenges")
        listOf(Triple("Review 10 cards", JI.Cards, "+20 XP"), Triple("Ask the tutor a question", JI.Tutor, "+15 XP"), Triple("Analyse one verb", JI.Tree, "+15 XP")).forEachIndexed { i, (title, ic, xp) ->
            JListItem(title, subtitle = if (i == 0) "Done" else "Open", icon = ic, trailing = {
                JText(xp, t.labelL, c.onSurfaceVariant)
                JIcon(JI.Chevron, size = 20.dp, tint = c.onSurfaceSubtle)
            })
        }
    }
}
