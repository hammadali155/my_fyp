package com.meher.jawhar.ui

import androidx.compose.foundation.background
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
import com.meher.jawhar.data.api.ApiClient
import com.meher.jawhar.theme.AppleEmerald
import com.meher.jawhar.theme.AppleGold

@Composable
fun SurahListView(
    onSurahSelected: (Surah) -> Unit,
) {
    var searchQuery by remember { mutableStateOf("") }
    var selectedFilterIndex by remember { mutableStateOf(0) } // 0: All, 1: Makkah, 2: Madinah
    var surahs by remember { mutableStateOf(QuranSampleData.sampleSurahs) }

    LaunchedEffect(Unit) {
        try {
            val api = ApiClient()
            surahs = api.getSurahs().map {
                Surah(
                    id = it.id,
                    number = it.number,
                    nameArabic = it.name_arabic,
                    nameTransliteration = it.name_transliteration,
                    nameEnglish = it.name_english,
                    revelationPlace = it.revelation_place,
                    verseCount = it.verse_count,
                )
            }
            api.close()
        } catch (_: Exception) {
            // keep sample data on any failure
        }
    }

    val filteredSurahs = remember(searchQuery, selectedFilterIndex, surahs) {
        val query = searchQuery.trim().lowercase()
        surahs.filter { surah ->
            val matchesFilter = when (selectedFilterIndex) {
                1 -> surah.revelationPlace.equals("Makkah", ignoreCase = true)
                2 -> surah.revelationPlace.equals("Madinah", ignoreCase = true)
                else -> true
            }
            val matchesSearch = query.isEmpty() ||
                surah.nameTransliteration.lowercase().contains(query) ||
                surah.nameEnglish.lowercase().contains(query) ||
                surah.nameArabic.contains(query) ||
                surah.number.toString() == query

            matchesFilter && matchesSearch
        }
    }

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background),
        contentPadding = PaddingValues(bottom = 100.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        // 1. Apple Large Title Header
        item {
            AppleLargeHeader(
                title = "Quran",
                subtitle = "CLASSICAL ARABIC & SARF",
                arabicTitle = "القُرآنُ الكَرِيم",
            )
        }

        // 2. Apple Daily Learning Progress Widget (Fitness / Rings style)
        item {
            AppleInsetCard {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Column(modifier = Modifier.weight(1f)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            ApplePillBadge(
                                text = "DAILY GOAL",
                                backgroundColor = MaterialTheme.colorScheme.primaryContainer,
                                textColor = MaterialTheme.colorScheme.primary,
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(
                                text = "🔥 5 Day Streak",
                                style = MaterialTheme.typography.labelSmall,
                                fontWeight = FontWeight.Bold,
                                color = AppleGold,
                            )
                        }
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            text = "Surah Al-Fatihah",
                            style = MaterialTheme.typography.titleLarge,
                            fontWeight = FontWeight.Bold,
                        )
                        Text(
                            text = "Ayah 1 to 7 • 29 Morphological Roots",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }

                    // Circular Progress Graphic
                    Box(
                        modifier = Modifier
                            .size(62.dp)
                            .clip(CircleShape)
                            .background(MaterialTheme.colorScheme.primaryContainer),
                        contentAlignment = Alignment.Center,
                    ) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Text(
                                text = "100%",
                                style = MaterialTheme.typography.labelLarge,
                                fontWeight = FontWeight.Bold,
                                color = MaterialTheme.colorScheme.primary,
                            )
                            Text(
                                text = "DONE",
                                fontSize = 8.sp,
                                fontWeight = FontWeight.Bold,
                                color = MaterialTheme.colorScheme.primary,
                            )
                        }
                    }
                }
            }
        }

        // 3. Apple Inset Search Field
        item {
            AppleSearchField(
                query = searchQuery,
                onQueryChange = { searchQuery = it },
                placeholder = "Search by Surah name, number, or Arabic...",
            )
        }

        // 4. Apple Segmented Control Filter
        item {
            AppleSegmentedControl(
                items = listOf("All", "Makkah", "Madinah"),
                selectedIndex = selectedFilterIndex,
                onIndexSelected = { selectedFilterIndex = it },
            )
        }

        // 5. Inset Section Header
        item {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 24.dp, vertical = 2.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text(
                    text = "SURAHS (${filteredSurahs.size})",
                    style = MaterialTheme.typography.labelSmall,
                    fontWeight = FontWeight.Bold,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    letterSpacing = 1.sp,
                )
                Text(
                    text = "REVELATION ORDER",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }

        // 6. Inset List of Surahs
        items(filteredSurahs, key = { it.id }) { surah ->
            AppleInsetCard(onClick = { onSurahSelected(surah) }) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.SpaceBetween,
                ) {
                    Row(
                        modifier = Modifier.weight(1f),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        // iOS Number Pill
                        Surface(
                            modifier = Modifier.size(42.dp),
                            shape = RoundedCornerShape(12.dp),
                            color = MaterialTheme.colorScheme.surfaceVariant,
                        ) {
                            Box(contentAlignment = Alignment.Center) {
                                Text(
                                    text = surah.number.toString(),
                                    style = MaterialTheme.typography.titleMedium,
                                    fontWeight = FontWeight.Bold,
                                    color = MaterialTheme.colorScheme.onSurface,
                                )
                            }
                        }

                        Spacer(modifier = Modifier.width(14.dp))

                        Column {
                            Text(
                                text = surah.nameTransliteration,
                                style = MaterialTheme.typography.titleMedium,
                                fontWeight = FontWeight.Bold,
                            )
                            Spacer(modifier = Modifier.height(2.dp))
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Text(
                                    text = surah.nameEnglish,
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                                )
                                Spacer(modifier = Modifier.width(6.dp))
                                Text(
                                    text = "•",
                                    fontSize = 10.sp,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                                )
                                Spacer(modifier = Modifier.width(6.dp))
                                Text(
                                    text = "${surah.verseCount} Verses",
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                                )
                            }
                        }
                    }

                    Column(horizontalAlignment = Alignment.End) {
                        Text(
                            text = surah.nameArabic,
                            fontSize = 24.sp,
                            fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.primary,
                        )
                        Spacer(modifier = Modifier.height(4.dp))
                        ApplePillBadge(
                            text = surah.revelationPlace ?: "Makkah",
                            backgroundColor = if (surah.revelationPlace == "Makkah") {
                                MaterialTheme.colorScheme.secondaryContainer
                            } else {
                                MaterialTheme.colorScheme.primaryContainer
                            },
                            textColor = if (surah.revelationPlace == "Makkah") {
                                MaterialTheme.colorScheme.secondary
                            } else {
                                MaterialTheme.colorScheme.primary
                            },
                        )
                    }
                }
            }
        }
    }
}
