package com.meher.jawhar.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxScope
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
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.meher.jawhar.design.*
import com.meher.jawhar.nav.Dest
import com.meher.jawhar.nav.LocalNav

@Composable
fun BoxScope.Composer(value: String, onValueChange: (String) -> Unit) {
    val c = Jawhar.colors
    val t = Jawhar.type
    val bottom = 22.dp + 68.dp + 12.dp + (LocalBottomInset.current - 24.dp).coerceAtLeast(0.dp)
    Row(
        Modifier
            .align(Alignment.BottomCenter)
            .fillMaxWidth()
            .padding(start = 24.dp, end = 24.dp, bottom = bottom)
            .height(56.dp)
            .softShadow(CapsuleShape, 14.dp, 0.3f)
            .clip(CapsuleShape)
            .background(c.bgSurface.copy(alpha = 0.95f))
            .padding(start = 20.dp, end = 6.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        BasicTextField(
            value = value,
            onValueChange = onValueChange,
            singleLine = true,
            textStyle = t.bodyM.copy(color = c.onSurface),
            cursorBrush = SolidColor(c.primary),
            modifier = Modifier.weight(1f),
            decorationBox = { inner ->
                Box(contentAlignment = Alignment.CenterStart) {
                    if (value.isEmpty()) JText("Ask the tutor anything", t.bodyM, c.onSurfaceSubtle)
                    inner()
                }
            },
        )
        JIcon(JI.Mic, size = 22.dp, tint = c.onSurfaceVariant)
        Box(Modifier.size(44.dp).clip(CircleShape).background(c.primary), contentAlignment = Alignment.Center) { JIcon(JI.Send, size = 20.dp, tint = c.onPrimary) }
    }
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun TutorChatScreen(error: Boolean = false) {
    val c = Jawhar.colors
    val t = Jawhar.type
    var draft by remember { mutableStateOf("") }
    Page(back = false, tab = JTab.Tutor, title = "AI Tutor", right = JI.More, overlay = { Composer(draft) { draft = it } }) {
        if (error) {
            JChatBubble("Why is رَبِّ in the genitive case?", true)
            Column(Modifier.fillMaxWidth().clip(SquircleShape(6.dp, 24.dp, 24.dp, 24.dp)).background(c.errorContainer).padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Row(horizontalArrangement = Arrangement.spacedBy(10.dp), verticalAlignment = Alignment.CenterVertically) {
                    JIcon(JI.Alert, size = 22.dp, tint = c.error)
                    JText("The reply did not come through", t.titleS, c.onSurface)
                }
                JText("The tutor lost the connection while answering.", t.bodyS, c.onSurfaceVariant)
                JButton("Retry", {}, Modifier.size(96.dp, 30.dp), height = 30.dp)
            }
        } else {
            Mock.chat.forEach { JChatBubble(it.text, it.fromUser) }
            JCard(Modifier.fillMaxWidth(0.88f), color = c.infoContainer, padding = 20.dp) {
                JText("KEY CONCEPT", t.labelS, c.info)
                JArabic("ٱلرَّحْمَٰنِ ٱلرَّحِيمِ", t.arabicQuranM, c.onSurface, Modifier.fillMaxWidth(), TextAlign.Start)
                listOf("Root" to "ر ح م", "Pattern" to "فَعْلَان", "Meaning" to "Most Gracious").forEach { (a, b) ->
                    Row(Modifier.fillMaxWidth().padding(top = 6.dp)) {
                        JText(a, t.labelM, c.onSurfaceVariant, Modifier.weight(1f))
                        JText(b, t.titleS, c.onSurface)
                    }
                }
            }
            Row(Modifier.clip(SquircleShape(6.dp, 20.dp, 20.dp, 20.dp)).background(c.bgSurfaceVariant).padding(horizontal = 20.dp, vertical = 16.dp), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                repeat(3) { Box(Modifier.size(7.dp).clip(CircleShape).background(c.onSurfaceSubtle.copy(alpha = 0.5f + it * 0.2f))) }
            }
            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                JChip("Show the word family", false, {})
                JChip("Quiz me", false, {})
            }
        }
    }
}

@Composable
fun TutorStartScreen() {
    val nav = LocalNav.current
    val c = Jawhar.colors
    val t = Jawhar.type
    var draft by remember { mutableStateOf("") }
    Page(back = false, tab = JTab.Tutor, title = "AI Tutor", right = JI.More, overlay = { Composer(draft) { draft = it } }) {
        Column(Modifier.fillMaxWidth().padding(top = 24.dp), horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Box(Modifier.size(88.dp).softShadow(CircleShape, 12.dp, 0.3f).clip(CircleShape).background(c.primary), contentAlignment = Alignment.Center) { JIcon(JI.Spark, size = 44.dp, tint = c.onPrimary) }
            Spacer(Modifier.height(8.dp))
            JText("What would you like to learn today?", t.headlineM, c.onSurface, textAlign = TextAlign.Center)
            JText("Ask about any ayah, word or grammar rule.", t.bodyM, c.onSurfaceVariant, textAlign = TextAlign.Center)
        }
        val tiles = listOf(
            Triple("Explain an ayah", JI.Doc, c.primaryContainer), Triple("Quiz me on roots", JI.Target, c.accentContainer),
            Triple("What is i'rab?", JI.Help, c.infoContainer), Triple("Practice verbs", JI.Tree, c.bgSurfaceVariant),
        )
        tiles.chunked(2).forEach { pair ->
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                pair.forEach { (label, ic, fill) ->
                    Column(Modifier.weight(1f).height(112.dp).clip(SquircleShape(28.dp)).background(fill).tappable { nav.go(Dest.TutorChat) }.padding(18.dp), verticalArrangement = Arrangement.SpaceBetween) {
                        Box(Modifier.size(36.dp).clip(CircleShape).background(c.bgSurface), contentAlignment = Alignment.Center) { JIcon(ic, size = 20.dp, tint = c.onPrimaryContainer) }
                        JText(label, t.titleS, c.onSurface)
                    }
                }
            }
        }
        JText("Past chats", t.labelL, c.primary, Modifier.fillMaxWidth().tappable { nav.go(Dest.TutorHistory) }, TextAlign.Center)
    }
}

@Composable
fun TutorHistoryScreen(empty: Boolean = false) {
    val nav = LocalNav.current
    val c = Jawhar.colors
    val t = Jawhar.type
    Page(title = "Past chats", right = JI.Search) {
        if (empty) {
            Spacer(Modifier.height(60.dp))
            JCenterState(JI.Tutor, c.infoContainer, c.info, "No chats yet", "Your conversations with the tutor will appear here.")
            JButton("Start a chat", { nav.go(Dest.TutorChat) }, Modifier.align(Alignment.CenterHorizontally).size(150.dp, 44.dp), JButtonStyle.Tonal, height = 44.dp)
        } else {
            JSectionLabel("Today")
            listOf("The root of الرَّحْمَٰن" to "4 messages · 8:12 PM", "Why is رَبِّ in the genitive?" to "6 messages · 2:40 PM").forEach { (a, b) -> HistoryRow(a, b) }
            JSectionLabel("This week")
            listOf("Quiz: Form I verbs" to "10 messages · Mon", "Explain i'rab of Al-Fatiha 1:2" to "5 messages · Sun").forEach { (a, b) -> HistoryRow(a, b) }
            JText("Swipe left on a chat to delete it", t.bodyS, c.onSurfaceSubtle, Modifier.fillMaxWidth(), TextAlign.Center)
        }
    }
}

@Composable
private fun HistoryRow(title: String, meta: String) {
    val nav = LocalNav.current
    JListItem(title, subtitle = meta, onClick = { nav.go(Dest.TutorChat) })
}
