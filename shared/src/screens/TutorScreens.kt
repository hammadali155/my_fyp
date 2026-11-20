package com.meher.jawhar.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
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
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.launch
import com.meher.jawhar.data.LocalApi
import com.meher.jawhar.data.api.TutorReferenceDto
import com.meher.jawhar.data.api.TutorSessionSummaryDto
import com.meher.jawhar.data.api.tutorChat
import com.meher.jawhar.data.api.tutorDeleteSession
import com.meher.jawhar.data.api.tutorSessions
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
fun TutorChatScreen() {
    val nav = LocalNav.current
    val api = LocalApi.current
    val c = Jawhar.colors
    val t = Jawhar.type
    val scope = rememberCoroutineScope()
    var draft by remember { mutableStateOf("") }
    var loading by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf(false) }
    var errorMessage by remember { mutableStateOf("") }
    var messages by remember { mutableStateOf<List<Pair<String, Boolean>>>(emptyList()) }
    var sessionId by remember { mutableStateOf<Int?>(null) }

    val reference = nav.currentArg as? TutorReferenceDto

    LaunchedEffect(reference) {
        if (reference != null && messages.isEmpty()) {
            scope.launch {
                loading = true
                try {
                    val res = api.tutorChat(
                        "Explain this word and its grammar in the Quran",
                        sessionId,
                        reference,
                    )
                    sessionId = res.session_id
                    messages = messages + listOf(
                        "Tell me about this word" to true,
                        res.reply to false,
                    )
                } catch (e: Exception) {
                    error = true
                    errorMessage = e.message ?: "Could not load tutor response"
                } finally {
                    loading = false
                }
            }
        }
    }

    fun onSend() {
        val msg = draft.trim()
        if (msg.isEmpty() || loading) return
        draft = ""
        val userMsg = msg to true
        messages = messages + userMsg
        scope.launch {
            loading = true
            try {
                val res = api.tutorChat(msg, sessionId, null)
                sessionId = res.session_id
                messages = messages + (res.reply to false)
            } catch (e: Exception) {
                error = true
                errorMessage = e.message ?: "The tutor did not respond"
            } finally {
                loading = false
            }
        }
    }

    Page(
        back = false,
        tab = JTab.Tutor,
        title = "AI Tutor",
        right = JI.More,
        scroll = false,
    ) {
        if (error) {
            Column(Modifier.fillMaxWidth().padding(top = 80.dp), horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(16.dp)) {
                StateScreen(JI.Alert, c.errorContainer, c.error, "Could not connect to tutor", errorMessage, "Try again", onPrimary = { loading = true; error = false }, back = true)
            }
        } else if (messages.isEmpty() && !loading) {
            Column(Modifier.fillMaxWidth().padding(top = 80.dp), horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(16.dp)) {
                StateScreen(JI.Tutor, c.infoContainer, c.info, "Start a conversation", "Ask anything about the Quran, Arabic grammar, or word meanings.", "New chat", onPrimary = { }, back = false)
            }
        } else {
            Column(
                Modifier.fillMaxWidth().verticalScroll(rememberScrollState()),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                if (loading) {
                    JSkeleton(Modifier.fillMaxWidth().height(80.dp), radius = 24.dp)
                    JSkeleton(Modifier.fillMaxWidth(0.7f).height(40.dp), radius = 20.dp)
                }
                messages.forEachIndexed { index, (text, fromUser) ->
                    val isLastLoading = loading && index == messages.lastIndex
                    JChatBubble(text, fromUser)
                    if (isLastLoading) {
                        Row(Modifier.padding(horizontal = 16.dp, vertical = 4.dp)) {
                            repeat(3) { Box(Modifier.size(7.dp).clip(CircleShape).background(c.onSurfaceSubtle.copy(alpha = 0.5f + it * 0.2f))) }
                        }
                    }
                }
                FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    JChip("Show the word family", false, {})
                    JChip("Quiz me", false, {})
                }
                Spacer(Modifier.height(100.dp))
            }
        }
        TutorInputBar(draft = draft, onValueChange = { draft = it }, onSend = ::onSend, loading = loading, c = c, t = t)
    }
}

@Composable
fun TutorInputBar(
    draft: String,
    onValueChange: (String) -> Unit,
    onSend: () -> Unit,
    loading: Boolean,
    c: JawharColors,
    t: JawharType,
) {
    Row(
        Modifier
            .fillMaxWidth()
            .padding(horizontal = 20.dp, vertical = 12.dp)
            .background(c.bgSurface.copy(alpha = 0.95f))
            .clip(CapsuleShape)
            .softShadow(CapsuleShape, 14.dp, 0.3f),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        BasicTextField(
            value = draft,
            onValueChange = onValueChange,
            singleLine = true,
            textStyle = t.bodyM.copy(color = c.onSurface),
            cursorBrush = SolidColor(c.primary),
            modifier = Modifier.fillMaxWidth(),
            decorationBox = { inner ->
                Box(contentAlignment = Alignment.CenterStart) {
                    if (draft.isEmpty()) JText("Ask the tutor anything", t.bodyM, c.onSurfaceSubtle)
                    inner()
                }
            },
        )
        JIcon(JI.Mic, size = 22.dp, tint = c.onSurfaceVariant)
        Box(
            Modifier.size(44.dp).clip(CircleShape).background(c.primary).tappable(onClick = { onSend() }),
            contentAlignment = Alignment.Center,
        ) {
            JIcon(JI.Send, size = 20.dp, tint = c.onPrimary)
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
fun TutorHistoryScreen() {
    val nav = LocalNav.current
    val api = LocalApi.current
    val c = Jawhar.colors
    val t = Jawhar.type
    val scope = rememberCoroutineScope()
    var sessions by remember { mutableStateOf<List<TutorSessionSummaryDto>>(emptyList()) }
    var loading by remember { mutableStateOf(true) }
    var error by remember { mutableStateOf(false) }
    var errorMessage by remember { mutableStateOf("") }

    LaunchedEffect(Unit) {
        try {
            sessions = api.tutorSessions().sessions
            error = false
        } catch (e: Exception) {
            error = true
            errorMessage = e.message ?: "Could not load chats"
        } finally {
            loading = false
        }
    }

    fun onDelete(sessionId: Int) {
        scope.launch {
            try {
                api.tutorDeleteSession(sessionId)
                sessions = sessions.filter { it.id != sessionId }
            } catch (e: Exception) {
                errorMessage = e.message ?: "Could not delete chat"
                error = true
            }
        }
    }

    Page(title = "Past chats", right = JI.Search) {
        if (error) {
            Column(Modifier.fillMaxWidth().padding(top = 80.dp), horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(16.dp)) {
                StateScreen(JI.Alert, c.errorContainer, c.error, "Could not load chats", errorMessage, "Try again", onPrimary = { loading = true; error = false }, back = true)
            }
        } else if (loading) {
            repeat(4) { JSkeleton(Modifier.fillMaxWidth().height(64.dp), radius = 20.dp) }
        } else if (sessions.isEmpty()) {
            StateScreen(JI.Tutor, c.infoContainer, c.info, "No chats yet", "Your conversations with the tutor will appear here.", "Start a chat", onPrimary = { nav.go(Dest.TutorChat) }, back = false)
        } else {
            sessions.forEach { s ->
                JListItem(
                    s.title,
                    subtitle = "${s.message_count} messages · ${s.updated_at.take(5)}",
                    icon = JI.Tutor,
                    onClick = { nav.go(Dest.TutorChat) },
                    trailing = {
                        Row(horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                            JIcon(JI.Chevron, size = 20.dp, tint = c.onSurfaceSubtle)
                            Box(Modifier.size(32.dp).clip(CircleShape).background(c.errorContainer).tappable(onClick = { onDelete(s.id) }), contentAlignment = Alignment.Center) {
                                JIcon(JI.Trash, size = 16.dp, tint = c.error)
                            }
                        }
                    },
                )
            }
            JText("Swipe left on a chat to delete it", t.bodyS, c.onSurfaceSubtle, Modifier.fillMaxWidth(), TextAlign.Center)
        }
    }
}
