package com.meher.jawhar.ui

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.expandVertically
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.shrinkVertically
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.meher.jawhar.data.QuranSampleData
import com.meher.jawhar.data.Surah
import com.meher.jawhar.data.Verse
import com.meher.jawhar.data.Word
import com.meher.jawhar.theme.AppleEmerald
import com.meher.jawhar.theme.AppleGold

@Composable
fun QuranReaderView(
    surah: Surah,
    onBack: () -> Unit,
) {
    var selectedWord by remember { mutableStateOf<Word?>(null) }
    var translationMode by remember { mutableStateOf(0) } // 0: English, 1: Urdu, 2: Both
    var bookmarkedVerses by remember { mutableStateOf(setOf<Int>()) }

    val verses = remember(surah.id) {
        if (surah.number == 1) {
            QuranSampleData.fatihahVerses
        } else {
            emptyList()
        }
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
    ) {
        LazyColumn(
            modifier = Modifier.fillMaxSize(),
            contentPadding = PaddingValues(bottom = 120.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            // 1. Apple Large Title Navigation Header
            item {
                AppleLargeHeader(
                    title = surah.nameTransliteration,
                    subtitle = "SURAH ${surah.number} • ${surah.verseCount} AYAH • ${surah.revelationPlace ?: "MAKKAH"}",
                    arabicTitle = surah.nameArabic,
                    onBackClick = onBack,
                )
            }

            // 2. Apple Segmented Control for Translation Mode
            item {
                AppleSegmentedControl(
                    items = listOf("English", "Urdu", "Bilingual"),
                    selectedIndex = translationMode,
                    onIndexSelected = { translationMode = it },
                )
            }

            // 3. Informational Inset Banner
            item {
                AppleInsetCard {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.SpaceBetween,
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text("💡", fontSize = 18.sp)
                            Spacer(modifier = Modifier.width(10.dp))
                            Text(
                                text = "Tap any word to inspect Root (جذر) & Grammar",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                            )
                        }
                        ApplePillBadge(
                            text = "SARF ACTIVE",
                            backgroundColor = MaterialTheme.colorScheme.primaryContainer,
                            textColor = MaterialTheme.colorScheme.primary,
                        )
                    }
                }
            }

            // 4. Bismillah Calligraphy Card (for Surahs other than At-Tawbah)
            if (surah.number != 9) {
                item {
                    AppleInsetCard {
                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(vertical = 12.dp),
                            contentAlignment = Alignment.Center,
                        ) {
                            Text(
                                text = "بِسْمِ ٱللَّهِ ٱلرَّحْمَـٰنِ ٱلرَّحِيمِ",
                                fontSize = 28.sp,
                                fontWeight = FontWeight.Bold,
                                color = MaterialTheme.colorScheme.primary,
                                textAlign = TextAlign.Center,
                            )
                        }
                    }
                }
            }

            // 5. Verse Cards List
            if (verses.isEmpty()) {
                item {
                    AppleInsetCard {
                        Column(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(vertical = 32.dp),
                            horizontalAlignment = Alignment.CenterHorizontally,
                        ) {
                            Text(
                                text = "Surah ${surah.nameTransliteration} (${surah.nameArabic})",
                                style = MaterialTheme.typography.titleLarge,
                                fontWeight = FontWeight.Bold,
                            )
                            Spacer(modifier = Modifier.height(8.dp))
                            Text(
                                text = "Verses are loaded dynamically via FastAPI backend.\nSurah Al-Fatihah is available in full offline interactive mode.",
                                style = MaterialTheme.typography.bodyMedium,
                                textAlign = TextAlign.Center,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                            )
                        }
                    }
                }
            } else {
                items(verses, key = { it.id }) { verse ->
                    AppleVerseCard(
                        verse = verse,
                        translationMode = translationMode,
                        isBookmarked = bookmarkedVerses.contains(verse.id),
                        onToggleBookmark = {
                            bookmarkedVerses = if (bookmarkedVerses.contains(verse.id)) {
                                bookmarkedVerses - verse.id
                            } else {
                                bookmarkedVerses + verse.id
                            }
                        },
                        selectedWord = selectedWord,
                        onWordClick = { word ->
                            selectedWord = if (selectedWord?.id == word.id) null else word
                        },
                    )
                }
            }
        }

        // Floating Morphology Inspector (iOS Modal Sheet)
        AnimatedVisibility(
            visible = selectedWord != null,
            modifier = Modifier.align(Alignment.BottomCenter),
            enter = fadeIn() + expandVertically(expandFrom = Alignment.Bottom),
            exit = fadeOut() + shrinkVertically(shrinkTowards = Alignment.Bottom),
        ) {
            if (selectedWord != null) {
                AppleMorphologyInspector(
                    word = selectedWord!!,
                    onDismiss = { selectedWord = null },
                )
            }
        }
    }
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun AppleVerseCard(
    verse: Verse,
    translationMode: Int,
    isBookmarked: Boolean,
    onToggleBookmark: () -> Unit,
    selectedWord: Word?,
    onWordClick: (Word) -> Unit,
) {
    AppleInsetCard {
        // Header: Ayah Number Circle & Action Buttons
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            // Circular iOS Ayah Badge
            Surface(
                modifier = Modifier.size(34.dp),
                shape = CircleShape,
                color = MaterialTheme.colorScheme.primaryContainer,
            ) {
                Box(contentAlignment = Alignment.Center) {
                    Text(
                        text = verse.ayahNumber.toString(),
                        style = MaterialTheme.typography.labelLarge,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.primary,
                    )
                }
            }

            // Quick Actions: Recite & Bookmark
            Row(verticalAlignment = Alignment.CenterVertically) {
                Surface(
                    modifier = Modifier
                        .size(32.dp)
                        .clip(CircleShape)
                        .clickable { /* Audio recitation hook */ },
                    shape = CircleShape,
                    color = MaterialTheme.colorScheme.surfaceVariant,
                ) {
                    Box(contentAlignment = Alignment.Center) {
                        Text("🔊", fontSize = 13.sp)
                    }
                }

                Spacer(modifier = Modifier.width(8.dp))

                Surface(
                    modifier = Modifier
                        .size(32.dp)
                        .clip(CircleShape)
                        .clickable(onClick = onToggleBookmark),
                    shape = CircleShape,
                    color = if (isBookmarked) MaterialTheme.colorScheme.secondaryContainer else MaterialTheme.colorScheme.surfaceVariant,
                ) {
                    Box(contentAlignment = Alignment.Center) {
                        Text(
                            text = if (isBookmarked) "★" else "☆",
                            fontSize = 15.sp,
                            color = if (isBookmarked) AppleGold else MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        // Uthmani Arabic Verse Typography
        Text(
            text = verse.textUthmani,
            fontSize = 26.sp,
            fontWeight = FontWeight.Bold,
            textAlign = TextAlign.End,
            lineHeight = 48.sp,
            color = MaterialTheme.colorScheme.onSurface,
            modifier = Modifier.fillMaxWidth(),
        )

        Spacer(modifier = Modifier.height(16.dp))

        // Interactive Word-by-Word Tokens (Apple Pills with Root Indicators)
        FlowRow(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(6.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            verse.words.forEach { word ->
                AppleWordChip(
                    word = word,
                    isSelected = selectedWord?.id == word.id,
                    onClick = { onWordClick(word) },
                )
            }
        }

        Spacer(modifier = Modifier.height(16.dp))
        HorizontalDivider(thickness = 0.5.dp, color = MaterialTheme.colorScheme.outlineVariant)
        Spacer(modifier = Modifier.height(12.dp))

        // English Translation (SF Pro Typography)
        if ((translationMode == 0 || translationMode == 2) && verse.translationEn != null) {
            Text(
                text = verse.translationEn,
                style = MaterialTheme.typography.bodyLarge,
                color = MaterialTheme.colorScheme.onSurface,
            )
        }

        // Urdu Translation
        if ((translationMode == 1 || translationMode == 2) && verse.translationUr != null) {
            if (translationMode == 2) {
                Spacer(modifier = Modifier.height(8.dp))
            }
            Text(
                text = verse.translationUr,
                fontSize = 18.sp,
                fontWeight = FontWeight.Medium,
                textAlign = TextAlign.End,
                color = MaterialTheme.colorScheme.primary,
                modifier = Modifier.fillMaxWidth(),
            )
        }
    }
}
