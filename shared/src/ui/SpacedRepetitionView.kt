package com.meher.jawhar.ui

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import kotlinx.coroutines.launch
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.meher.jawhar.data.api.srsDue
import com.meher.jawhar.data.api.srsReview
import com.meher.jawhar.theme.*

data class DrillCard(
    val id: Int,
    val wordArabic: String,
    val surahContext: String,
    val root: String,
    val lemma: String,
    val translation: String,
    val posTag: String,
)

fun srsCardToDrill(c: com.meher.jawhar.data.api.SrsCardDto): DrillCard = DrillCard(
    id = c.id,
    wordArabic = c.front,
    surahContext = "",
    root = c.word_root ?: "",
    lemma = "",
    translation = c.back,
    posTag = c.word_pos_tag ?: c.state,
)

val sampleDrillCards = listOf(
    DrillCard(1, "نَسْتَعِينُ", "Al-Fatihah 1:5", "عون", "اسْتَعَانَ", "we ask for help", "Verb Form X"),
    DrillCard(2, "ٱلرَّحْمَـٰنِ", "Al-Fatihah 1:1", "رحم", "رَحْمَن", "the Entirely Merciful", "Adjective"),
    DrillCard(3, "ٱلْمُسْتَقِيمَ", "Al-Fatihah 1:6", "قوم", "مُسْتَقِيم", "the straight path", "Active Participle"),
    DrillCard(4, "ٱلْمَغْضُوبِ", "Al-Fatihah 1:7", "غضب", "مَغْضُوب", "those who evoked wrath", "Passive Participle"),
)

@Composable
fun SpacedRepetitionView() {
    var cardIndex by remember { mutableStateOf(0) }
    var isFlipped by remember { mutableStateOf(false) }
    var xpEarned by remember { mutableStateOf(120) }
    var reviewsCompleted by remember { mutableStateOf(0) }
    var loggedIn by remember { mutableStateOf(com.meher.jawhar.data.api.Session.accessToken != null) }
    var liveCards by remember { mutableStateOf<List<DrillCard>>(emptyList()) }
    var liveError by remember { mutableStateOf<String?>(null) }
    val scope = androidx.compose.runtime.rememberCoroutineScope()

    if (!loggedIn) {
        LoginGate(onLoggedIn = { loggedIn = true })
        return
    }

    LaunchedEffect(Unit) {
        try {
            val api = com.meher.jawhar.data.api.ApiClient()
            liveCards = api.srsDue().map { srsCardToDrill(it) }
        } catch (e: Exception) {
            liveError = e.message
        }
    }

    if (liveError != null) {
        Text("Could not load due cards: $liveError", color = MaterialTheme.colorScheme.error, modifier = Modifier.padding(16.dp))
    }

    val sourceCards = if (liveCards.isNotEmpty()) liveCards else sampleDrillCards
    val currentCard = sourceCards.getOrNull(cardIndex % sourceCards.size)

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background),
        contentPadding = PaddingValues(bottom = 120.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        // 1. Apple Header
        item {
            AppleLargeHeader(
                title = "SRS Drills",
                subtitle = "SM-2 MEMORY RETENTION ENGINE",
                arabicTitle = "التَّكْرَارُ المُتَبَاعِد",
            )
        }

        // 2. Daily Review Stats Inset Card
        item {
            AppleInsetCard {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Surface(
                            shape = CircleShape,
                            color = MaterialTheme.colorScheme.primaryContainer,
                            modifier = Modifier.size(44.dp),
                        ) {
                            Box(contentAlignment = Alignment.Center) {
                                Text("⚡", fontSize = 20.sp)
                            }
                        }
                        Spacer(modifier = Modifier.width(12.dp))
                        Column {
                            Text(
                                text = "Daily Review Session",
                                style = MaterialTheme.typography.titleMedium,
                                fontWeight = FontWeight.Bold,
                            )
                            Text(
                                text = "${sampleDrillCards.size - (cardIndex % sampleDrillCards.size)} Cards Remaining Today",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                            )
                        }
                    }

                    ApplePillBadge(
                        text = "$xpEarned XP",
                        backgroundColor = MaterialTheme.colorScheme.secondaryContainer,
                        textColor = MaterialTheme.colorScheme.secondary,
                    )
                }
            }
        }

        // 3. Apple Interactive Flashcard
        if (currentCard != null) {
            item {
                AppleInsetCard(
                    modifier = Modifier.height(300.dp),
                    onClick = { isFlipped = !isFlipped },
                ) {
                    Column(
                        modifier = Modifier.fillMaxSize(),
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.SpaceBetween,
                    ) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                        ) {
                            ApplePillBadge(
                                text = currentCard.surahContext,
                                backgroundColor = MaterialTheme.colorScheme.surfaceVariant,
                                textColor = MaterialTheme.colorScheme.onSurface,
                            )
                            Text(
                                text = if (isFlipped) "Tap to flip back" else "Tap to reveal answer",
                                style = MaterialTheme.typography.labelSmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                            )
                        }

                        // Card Front / Back Content
                        Column(
                            horizontalAlignment = Alignment.CenterHorizontally,
                            verticalArrangement = Arrangement.Center,
                            modifier = Modifier.weight(1f),
                        ) {
                            Text(
                                text = currentCard.wordArabic,
                                fontSize = 42.sp,
                                fontWeight = FontWeight.Bold,
                                color = MaterialTheme.colorScheme.onSurface,
                            )
                            Spacer(modifier = Modifier.height(8.dp))

                            if (!isFlipped) {
                                Text(
                                    text = "Identify the 3-letter root (جذر) & meaning",
                                    style = MaterialTheme.typography.bodyMedium,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                                )
                            } else {
                                AnimatedVisibility(visible = isFlipped, enter = fadeIn(), exit = fadeOut()) {
                                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                        Text(
                                            text = "Root: ${currentCard.root}",
                                            style = MaterialTheme.typography.headlineMedium,
                                            fontWeight = FontWeight.Bold,
                                            color = MaterialTheme.colorScheme.primary,
                                        )
                                        Spacer(modifier = Modifier.height(4.dp))
                                        Text(
                                            text = "Meaning: \"${currentCard.translation}\"",
                                            style = MaterialTheme.typography.bodyLarge,
                                            fontWeight = FontWeight.Medium,
                                        )
                                        Spacer(modifier = Modifier.height(4.dp))
                                        ApplePillBadge(
                                            text = "${currentCard.lemma} • ${currentCard.posTag}",
                                            backgroundColor = MaterialTheme.colorScheme.secondaryContainer,
                                            textColor = MaterialTheme.colorScheme.secondary,
                                        )
                                    }
                                }
                            }
                        }

                        // Bottom card footer
                        Text(
                            text = "SM-2 Interval Factor: 2.50",
                            style = MaterialTheme.typography.labelSmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                }
            }

            // 4. Apple Rating Bar (Again, Hard, Good, Easy)
            item {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 20.dp),
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    // Rating 1: Again
                    Surface(
                        modifier = Modifier
                            .weight(1f)
                            .height(48.dp)
                            .clickable {
                                if (liveCards.isNotEmpty()) {
                                    scope.launch {
                                        try { com.meher.jawhar.data.api.ApiClient().srsReview(sourceCards[cardIndex % sourceCards.size].id, 1) } catch (_: Exception) {}
                                    }
                                }
                                cardIndex++
                                isFlipped = false
                                reviewsCompleted++
                            },
                        shape = RoundedCornerShape(14.dp),
                        color = MaterialTheme.colorScheme.surface,
                        border = BorderStroke(1.dp, AppleDestructive.copy(alpha = 0.4f)),
                    ) {
                        Column(
                            horizontalAlignment = Alignment.CenterHorizontally,
                            verticalArrangement = Arrangement.Center,
                        ) {
                            Text("Again", style = MaterialTheme.typography.labelMedium, fontWeight = FontWeight.Bold, color = AppleDestructive)
                            Text("<10m", fontSize = 10.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        }
                    }

                    // Rating 2: Hard
                    Surface(
                        modifier = Modifier
                            .weight(1f)
                            .height(48.dp)
                            .clickable {
                                if (liveCards.isNotEmpty()) {
                                    scope.launch {
                                        try { com.meher.jawhar.data.api.ApiClient().srsReview(sourceCards[cardIndex % sourceCards.size].id, 2) } catch (_: Exception) {}
                                    }
                                }
                                cardIndex++
                                isFlipped = false
                                xpEarned += 5
                                reviewsCompleted++
                            },
                        shape = RoundedCornerShape(14.dp),
                        color = MaterialTheme.colorScheme.surface,
                        border = BorderStroke(1.dp, AppleWarning.copy(alpha = 0.4f)),
                    ) {
                        Column(
                            horizontalAlignment = Alignment.CenterHorizontally,
                            verticalArrangement = Arrangement.Center,
                        ) {
                            Text("Hard", style = MaterialTheme.typography.labelMedium, fontWeight = FontWeight.Bold, color = AppleWarning)
                            Text("1 day", fontSize = 10.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        }
                    }

                    // Rating 3: Good
                    Surface(
                        modifier = Modifier
                            .weight(1f)
                            .height(48.dp)
                            .clickable {
                                if (liveCards.isNotEmpty()) {
                                    scope.launch {
                                        try { com.meher.jawhar.data.api.ApiClient().srsReview(sourceCards[cardIndex % sourceCards.size].id, 3) } catch (_: Exception) {}
                                    }
                                }
                                cardIndex++
                                isFlipped = false
                                xpEarned += 10
                                reviewsCompleted++
                            },
                        shape = RoundedCornerShape(14.dp),
                        color = MaterialTheme.colorScheme.surface,
                        border = BorderStroke(1.dp, AppleSuccess.copy(alpha = 0.4f)),
                    ) {
                        Column(
                            horizontalAlignment = Alignment.CenterHorizontally,
                            verticalArrangement = Arrangement.Center,
                        ) {
                            Text("Good", style = MaterialTheme.typography.labelMedium, fontWeight = FontWeight.Bold, color = AppleSuccess)
                            Text("3 days", fontSize = 10.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        }
                    }

                    // Rating 4: Easy
                    Surface(
                        modifier = Modifier
                            .weight(1f)
                            .height(48.dp)
                            .clickable {
                                if (liveCards.isNotEmpty()) {
                                    scope.launch {
                                        try { com.meher.jawhar.data.api.ApiClient().srsReview(sourceCards[cardIndex % sourceCards.size].id, 4) } catch (_: Exception) {}
                                    }
                                }
                                cardIndex++
                                isFlipped = false
                                xpEarned += 15
                                reviewsCompleted++
                            },
                        shape = RoundedCornerShape(14.dp),
                        color = MaterialTheme.colorScheme.primaryContainer,
                    ) {
                        Column(
                            horizontalAlignment = Alignment.CenterHorizontally,
                            verticalArrangement = Arrangement.Center,
                        ) {
                            Text("Easy", style = MaterialTheme.typography.labelMedium, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.primary)
                            Text("7 days", fontSize = 10.sp, color = MaterialTheme.colorScheme.primary)
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun LoginGate(onLoggedIn: () -> Unit) {
    val scope = androidx.compose.runtime.rememberCoroutineScope()
    var email by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var error by remember { mutableStateOf<String?>(null) }
    var loading by remember { mutableStateOf(false) }

    Column(modifier = Modifier.fillMaxSize().padding(24.dp), verticalArrangement = Arrangement.Center, horizontalAlignment = Alignment.CenterHorizontally) {
        Text("Sign in to sync your reviews", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
        OutlinedTextField(value = email, onValueChange = { email = it }, label = { Text("Email") })
        OutlinedTextField(value = password, onValueChange = { password = it }, label = { Text("Password") }, visualTransformation = androidx.compose.ui.text.input.PasswordVisualTransformation())
        Button(onClick = {
            loading = true
            error = null
            scope.launch {
                try {
                    com.meher.jawhar.data.api.AuthApi.login(com.meher.jawhar.data.api.ApiClient(), email, password)
                    onLoggedIn()
                } catch (e: Exception) {
                    error = e.message
                } finally {
                    loading = false
                }
            }
        }) { Text(if (loading) "..." else "Log in") }
        if (error != null) Text(error!!, color = MaterialTheme.colorScheme.error)
    }
}
