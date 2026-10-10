package com.meher.jawhar

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.meher.jawhar.data.QuranSampleData
import com.meher.jawhar.data.Surah
import com.meher.jawhar.theme.JawharTheme
import com.meher.jawhar.ui.MorphologyLabView
import com.meher.jawhar.ui.QuranReaderView
import com.meher.jawhar.ui.SpacedRepetitionView
import com.meher.jawhar.ui.SurahListView
import org.jetbrains.compose.reload.DevelopmentEntryPoint

@Composable
fun LegacyApp() {
    JawharTheme {
        var selectedSurah by remember { mutableStateOf<Surah?>(null) }
        var currentTab by remember { mutableStateOf(0) } // 0: Quran, 1: Sarf Lab, 2: Drills

        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(MaterialTheme.colorScheme.background),
        ) {
            // Screen Content
            if (selectedSurah != null) {
                QuranReaderView(
                    surah = selectedSurah!!,
                    onBack = { selectedSurah = null },
                )
            } else {
                when (currentTab) {
                    0 -> SurahListView(onSurahSelected = { selectedSurah = it })
                    1 -> MorphologyLabView()
                    2 -> SpacedRepetitionView()
                }
            }

            // Apple Floating Liquid Glass Tab Bar (Hidden in Reader View)
            if (selectedSurah == null) {
                Surface(
                    modifier = Modifier
                        .align(Alignment.BottomCenter)
                        .padding(horizontal = 24.dp, vertical = 20.dp)
                        .fillMaxWidth()
                        .height(64.dp)
                        .shadow(16.dp, RoundedCornerShape(32.dp)),
                    shape = RoundedCornerShape(32.dp),
                    color = MaterialTheme.colorScheme.surface.copy(alpha = 0.94f),
                    border = BorderStroke(0.5.dp, MaterialTheme.colorScheme.outlineVariant),
                ) {
                    Row(
                        modifier = Modifier
                            .fillMaxSize()
                            .padding(horizontal = 8.dp),
                        horizontalArrangement = Arrangement.SpaceAround,
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        AppleTabItem(
                            icon = "📖",
                            label = "Quran",
                            isSelected = currentTab == 0,
                            onClick = { currentTab = 0 },
                        )
                        AppleTabItem(
                            icon = "🔬",
                            label = "Sarf Lab",
                            isSelected = currentTab == 1,
                            onClick = { currentTab = 1 },
                        )
                        AppleTabItem(
                            icon = "⚡",
                            label = "SRS Drills",
                            isSelected = currentTab == 2,
                            onClick = { currentTab = 2 },
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun AppleTabItem(
    icon: String,
    label: String,
    isSelected: Boolean,
    onClick: () -> Unit,
) {
    val contentColor = if (isSelected) {
        MaterialTheme.colorScheme.primary
    } else {
        MaterialTheme.colorScheme.onSurfaceVariant
    }

    Column(
        modifier = Modifier
            .clip(RoundedCornerShape(20.dp))
            .clickable(onClick = onClick)
            .padding(horizontal = 16.dp, vertical = 6.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center,
    ) {
        Text(text = icon, fontSize = 20.sp)
        Spacer(modifier = Modifier.height(2.dp))
        Text(
            text = label,
            fontSize = 11.sp,
            fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal,
            color = contentColor,
        )
    }
}
