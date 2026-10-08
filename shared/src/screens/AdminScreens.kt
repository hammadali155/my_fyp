package com.meher.jawhar.screens

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.StrokeJoin
import androidx.compose.ui.graphics.drawscope.Fill
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.meher.jawhar.design.*
import com.meher.jawhar.nav.LocalNav

private val AdminNav = listOf("Overview" to JI.Grid, "Users" to JI.Users, "Content" to JI.Doc, "Vocabulary" to JI.Cards, "Challenges" to JI.Target, "Notifications" to JI.Bell, "Analytics" to JI.Chart)

@Composable
fun AdminShell(active: String, title: String, subtitle: String, content: @Composable ColumnScope.() -> Unit) {
    val nav = LocalNav.current
    val c = Jawhar.colors
    val t = Jawhar.type
    Row(Modifier.fillMaxSize().background(c.bgBase).padding(16.dp), horizontalArrangement = Arrangement.spacedBy(24.dp)) {
        Column(Modifier.width(248.dp).fillMaxHeight().clip(SquircleShape(34.dp)).background(c.bgInverse).padding(24.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp), modifier = Modifier.padding(bottom = 24.dp)) {
                JLogoMark(size = 44.dp)
                Column {
                    JText("Jawhar", t.titleM, c.onInverse)
                    JText("Admin", t.labelM, c.accent)
                }
            }
            AdminNav.forEach { (label, ic) ->
                val on = label == active
                val target = when (label) { "Overview" -> "admin_overview"; "Users" -> "admin_users"; "Content" -> "admin_content"; else -> null }
                Row(
                    Modifier.fillMaxWidth().height(48.dp).clip(CapsuleShape).background(if (on) c.onInverse.copy(alpha = 0.14f) else androidx.compose.ui.graphics.Color.Transparent)
                        .tappable { if (target != null) nav.reset(target) }.padding(horizontal = 20.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(14.dp),
                ) {
                    JIcon(ic, size = 22.dp, tint = c.onInverse.copy(alpha = if (on) 1f else 0.65f))
                    JText(label, t.titleS, c.onInverse.copy(alpha = if (on) 1f else 0.65f))
                }
            }
            Spacer(Modifier.weight(1f))
            Row(Modifier.fillMaxWidth().clip(SquircleShape(26.dp)).background(c.onInverse.copy(alpha = 0.08f)).padding(14.dp), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                JAvatar("HA", size = 40.dp)
                Column {
                    JText("Hammad Ali", t.titleS, c.onInverse)
                    JText("Super admin", t.bodyS, c.onInverse.copy(alpha = 0.65f))
                }
            }
        }
        Column(Modifier.weight(1f).verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(20.dp)) {
            Row(Modifier.fillMaxWidth().padding(top = 16.dp), verticalAlignment = Alignment.CenterVertically) {
                Column(Modifier.weight(1f)) {
                    JText(title, t.headlineL, c.onSurface)
                    JText(subtitle, t.bodyM, c.onSurfaceVariant)
                }
                JSearchField("", {}, "Search", Modifier.width(300.dp))
                Spacer(Modifier.width(16.dp))
                JAvatar("HA", size = 48.dp)
            }
            content()
            Spacer(Modifier.height(24.dp))
        }
    }
}

@Composable
fun AdminLoginScreen() {
    val c = Jawhar.colors
    val t = Jawhar.type
    val nav = LocalNav.current
    Row(Modifier.fillMaxSize()) {
        Box(Modifier.weight(1f).fillMaxHeight().background(c.bgInverse).starOrnaments(c.accent, StarSpec(120.dp, 140.dp, 520.dp, 0.18f), StarSpec(560.dp, 700.dp, 560.dp, 0.14f))) {
            JLogoMark(Modifier.padding(72.dp), size = 64.dp)
            Column(Modifier.align(Alignment.CenterStart).padding(horizontal = 72.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
                JText("Manage what learners see", t.displayL, c.onInverse)
                JText("Edit lessons, review analytics and keep Jawhar accurate for every learner.", t.bodyL, c.onInverse.copy(alpha = 0.75f), Modifier.width(480.dp))
            }
        }
        Box(Modifier.weight(1f).fillMaxHeight(), contentAlignment = Alignment.Center) {
            Column(Modifier.width(440.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
                BigTitle("Admin sign in", "Use your admin account to continue.")
                StatefulField("Email", "admin@jawhar.app", trailing = JI.Mail)
                StatefulField("Password", "••••••••••", password = true)
                JText("Forgot password?", t.labelL, c.primary, Modifier.fillMaxWidth(), TextAlign.End)
                JButton("Sign in", { nav.reset("admin_overview") })
            }
        }
    }
}

@Composable
fun AdminOverviewScreen() {
    val c = Jawhar.colors
    val t = Jawhar.type
    AdminShell("Overview", "Overview", "Learner activity over the last 30 days") {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(20.dp)) {
            listOf(Triple("Active learners", "1,284", "+8%"), Triple("Avg session", "14 min", "+2 min"), Triple("Lessons completed", "9,640", "+12%"), Triple("Review retention", "87%", "+3%")).forEachIndexed { i, (l, v, d) ->
                val fill = listOf(c.bgSurfaceVariant, c.primaryContainer, c.accentContainer, c.infoContainer)[i]
                JCard(Modifier.weight(1f), color = fill, padding = 24.dp) {
                    JText(l, t.labelL, c.onSurfaceVariant)
                    JText(v, t.headlineL, c.onSurface)
                    Spacer(Modifier.height(8.dp))
                    JTag(d, background = c.bgSurface, color = c.success, height = 26.dp)
                }
            }
        }
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(20.dp)) {
            JCard(Modifier.weight(1.9f), radius = 34.dp, padding = 28.dp) {
                JText("Daily active users", t.titleL, c.onSurface)
                val data = listOf(420f, 455f, 430f, 480f, 520f, 505f, 560f, 540f, 590f, 610f, 585f, 640f, 670f, 690f)
                Canvas(Modifier.fillMaxWidth().height(220.dp).padding(top = 20.dp)) {
                    val w = size.width
                    val h = size.height
                    val pts = data.mapIndexed { i, v -> Offset(i * w / (data.size - 1), h - v / 800f * h) }
                    for (g in 0..4) drawLine(c.outlineVariant, Offset(0f, h * g / 4f), Offset(w, h * g / 4f), 1.dp.toPx())
                    val area = Path().apply {
                        moveTo(pts.first().x, h)
                        pts.forEach { lineTo(it.x, it.y) }
                        lineTo(pts.last().x, h)
                        close()
                    }
                    drawPath(area, c.primary.copy(alpha = 0.12f), style = Fill)
                    val line = Path().apply { pts.forEachIndexed { i, p -> if (i == 0) moveTo(p.x, p.y) else lineTo(p.x, p.y) } }
                    drawPath(line, c.primary, style = Stroke(3.dp.toPx(), cap = StrokeCap.Round, join = StrokeJoin.Round))
                    drawCircle(c.accent, 7.dp.toPx(), pts.last())
                }
            }
            JCard(Modifier.weight(1f), color = c.primaryContainer, radius = 34.dp, padding = 28.dp) {
                JText("Module usage", t.titleL, c.onSurface)
                Spacer(Modifier.height(16.dp))
                listOf("AI Tutor" to 0.91f, "Flashcards" to 0.85f, "Sarf Engine" to 0.78f, "Nahw Parser" to 0.64f).forEach { (l, v) ->
                    Row(Modifier.fillMaxWidth()) {
                        JText(l, t.titleS, c.onSurface, Modifier.weight(1f))
                        JText("${(v * 100).toInt()}%", t.labelL, c.onPrimaryContainer)
                    }
                    JProgressBar(v, Modifier.fillMaxWidth().padding(top = 6.dp, bottom = 16.dp), height = 10.dp, track = c.bgSurface)
                }
            }
        }
        JCard(Modifier.fillMaxWidth(), radius = 34.dp, padding = 28.dp) {
            JText("Topics learners struggle with", t.titleL, c.onSurface)
            Spacer(Modifier.height(12.dp))
            listOf(Triple("Case endings of the mudaf ilayh", "Nahw", 0.38f), Triple("Form VIII verb patterns", "Sarf", 0.44f), Triple("Hollow verb conjugation", "Sarf", 0.49f)).forEach { (topic, skill, acc) ->
                Row(Modifier.fillMaxWidth().padding(vertical = 10.dp), verticalAlignment = Alignment.CenterVertically) {
                    JText(topic, t.titleS, c.onSurface, Modifier.weight(2f))
                    JTag(skill, height = 26.dp)
                    JProgressBar(acc, Modifier.weight(1.4f).padding(horizontal = 24.dp), track = c.bgSurfaceHigh, fill = c.error)
                    JText("${(acc * 100).toInt()}%", t.labelL, c.onSurfaceVariant)
                }
            }
        }
    }
}

@Composable
fun AdminUsersScreen() {
    val c = Jawhar.colors
    val t = Jawhar.type
    var filter by remember { mutableStateOf(0) }
    val users = listOf(
        listOf("Meher Ali", "meher@email.com", "Learner", "Beginner II", "2,480", "Today"), listOf("Sara Khan", "sara.k@email.com", "Learner", "Intermediate I", "3,240", "Today"),
        listOf("Hammad Ali", "hammad@jawhar.app", "Admin", "Advanced", "5,910", "Today"), listOf("Bilal Raza", "bilal.r@email.com", "Learner", "Beginner III", "2,760", "Yesterday"),
        listOf("Ayesha Malik", "ayesha.m@email.com", "Editor", "Intermediate II", "4,120", "2 days ago"), listOf("Usman Tariq", "usman.t@email.com", "Learner", "Beginner I", "610", "9 days ago"),
    )
    AdminShell("Users", "Users", "1,284 learners · 6 editors · 2 admins") {
        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            JSearchField("", {}, "Search by name or email", Modifier.width(360.dp))
            listOf("All", "Learners", "Editors", "Admins").forEachIndexed { i, l -> JChip(l, filter == i, { filter = i }) }
            Spacer(Modifier.weight(1f))
            JButton("Invite user", {}, Modifier.width(150.dp), icon = JI.Plus, height = 48.dp)
        }
        JCard(Modifier.fillMaxWidth(), radius = 34.dp, padding = 28.dp) {
            Row(Modifier.fillMaxWidth().padding(bottom = 12.dp)) {
                listOf("USER" to 3f, "ROLE" to 1.2f, "LEVEL" to 1.4f, "XP" to 1f, "LAST ACTIVE" to 1.4f).forEach { (h, w) -> JText(h, t.labelS, c.onSurfaceSubtle, Modifier.weight(w)) }
            }
            users.forEach { u ->
                Row(Modifier.fillMaxWidth().padding(vertical = 10.dp), verticalAlignment = Alignment.CenterVertically) {
                    Row(Modifier.weight(3f), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(14.dp)) {
                        JAvatar(u[0].take(1) + u[0].substringAfter(" ").take(1), size = 44.dp)
                        Column { JText(u[0], t.titleS, c.onSurface); JText(u[1], t.bodyS, c.onSurfaceVariant) }
                    }
                    Box(Modifier.weight(1.2f)) {
                        JTag(u[2], background = when (u[2]) { "Admin" -> c.accentContainer; "Editor" -> c.infoContainer; else -> c.bgSurface }, color = when (u[2]) { "Admin" -> c.onAccentContainer; "Editor" -> c.info; else -> c.onSurface }, height = 28.dp)
                    }
                    JText(u[3], t.bodyM, c.onSurface, Modifier.weight(1.4f))
                    JText(u[4], t.bodyM, c.onSurface, Modifier.weight(1f))
                    JText(u[5], t.bodyM, c.onSurfaceVariant, Modifier.weight(1.4f))
                }
            }
        }
    }
}

@Composable
fun AdminContentScreen() {
    val c = Jawhar.colors
    val t = Jawhar.type
    var selected by remember { mutableStateOf(0) }
    val lessons = listOf("Form I: Fa'ala" to "Published", "Present tense" to "Published", "Command form" to "Draft", "Form II" to "Draft", "Active participle" to "Published")
    AdminShell("Content", "Content", "Lessons and quiz questions") {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(20.dp)) {
            JCard(Modifier.width(340.dp), radius = 34.dp, padding = 16.dp) {
                JText("Lessons", t.titleL, c.onSurface, Modifier.padding(12.dp))
                lessons.forEachIndexed { i, (name, status) ->
                    Column(Modifier.fillMaxWidth().clip(SquircleShape(24.dp)).background(if (i == selected) c.primaryContainer else androidx.compose.ui.graphics.Color.Transparent).tappable { selected = i }.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                        JText(name, t.titleS, c.onSurface)
                        JTag(status, background = if (status == "Published") c.successContainer else c.accentContainer, color = if (status == "Published") c.success else c.onAccentContainer, height = 22.dp)
                    }
                }
            }
            JCard(Modifier.weight(1f), radius = 34.dp, padding = 32.dp) {
                JText(lessons[selected].first, t.headlineS, c.onSurface)
                Spacer(Modifier.height(16.dp))
                StatefulField("Lesson title", lessons[selected].first, trailing = JI.Edit)
                Spacer(Modifier.height(16.dp))
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(20.dp)) {
                    Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                        JText("Explanation (English)", t.labelM, c.onSurfaceVariant)
                        Box(Modifier.fillMaxWidth().height(130.dp).clip(SquircleShape(22.dp)).background(c.bgSurface).padding(20.dp)) {
                            JText("Put the three root letters on the pattern, and each letter takes a fatha.", t.bodyM, c.onSurface)
                        }
                    }
                    Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                        JText("Example word (Arabic)", t.labelM, c.onSurfaceVariant)
                        Box(Modifier.fillMaxWidth().height(130.dp).clip(SquircleShape(22.dp)).background(c.bgSurface).padding(20.dp), contentAlignment = Alignment.CenterStart) {
                            JArabic("كَتَبَ", t.arabicWordL, c.onSurface, Modifier.fillMaxWidth())
                        }
                    }
                }
                Spacer(Modifier.height(20.dp))
                JText("Quiz question 1", t.titleM, c.onSurface)
                Spacer(Modifier.height(8.dp))
                Box(Modifier.fillMaxWidth().clip(SquircleShape(22.dp)).background(c.bgSurface).padding(20.dp)) { JText("Which word is the active participle of كَتَبَ?", t.bodyL, c.onSurface) }
                Spacer(Modifier.height(8.dp))
                listOf("كَاتِبٌ", "مَكْتُوبٌ", "كِتَابٌ", "مَكْتَبٌ").chunked(2).forEachIndexed { r, pair ->
                    Row(Modifier.fillMaxWidth().padding(bottom = 8.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        pair.forEachIndexed { k, w ->
                            val correct = r == 0 && k == 0
                            Row(Modifier.weight(1f).height(52.dp).clip(SquircleShape(20.dp)).background(if (correct) c.successContainer else c.bgSurface).padding(horizontal = 16.dp), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                                Box(Modifier.size(22.dp).clip(CircleShape).background(if (correct) c.success else c.bgSurfaceHigh))
                                JArabic(w, t.arabicTitle, c.onSurface)
                            }
                        }
                    }
                }
                Row(Modifier.fillMaxWidth().padding(top = 12.dp), horizontalArrangement = Arrangement.End, verticalAlignment = Alignment.CenterVertically) {
                    JButton("Save draft", {}, Modifier.width(150.dp), JButtonStyle.Neutral, height = 48.dp)
                    Spacer(Modifier.width(12.dp))
                    JButton("Publish", {}, Modifier.width(140.dp), height = 48.dp)
                }
            }
        }
    }
}
