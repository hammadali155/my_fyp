package com.meher.jawhar.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.meher.jawhar.theme.AppleEmerald
import com.meher.jawhar.theme.AppleGold

data class VerbFormDisplay(
    val formNumber: Int,
    val name: String = "",
    val patternPast: String,
    val patternPresent: String,
    val verbalNoun: String,
    val description: String,
    val example: String,
)

val sampleForms = listOf(
    VerbFormDisplay(1, "Form I", "فَعَلَ", "يَفْعَلُ", "فَعْل / فُعُول", "Base primary stem representing the fundamental verbal root meaning.", "كَتَبَ (He wrote)"),
    VerbFormDisplay(2, "Form II", "فَعَّلَ", "يُفَعِّلُ", "تَفْعِيل", "Causative, intensive, or declarative meaning.", "عَلَّمَ (He taught)"),
    VerbFormDisplay(3, "Form III", "فَاعَلَ", "يُفَاعِلُ", "مُفَاعَلَة / فِعَال", "Reciprocity, association, or striving towards an action.", "جَاهَدَ (He strove)"),
    VerbFormDisplay(4, "Form IV", "أَفْعَلَ", "يُفْعِلُ", "إِفْعَال", "Transitive or causative stem.", "أَنْزَلَ (He sent down)"),
    VerbFormDisplay(5, "Form V", "تَفَعَّلَ", "يَتَفَعَّلُ", "تَفَعُّل", "Reflexive of Form II; gradual or reflective action.", "تَذَكَّرَ (He reflected)"),
    VerbFormDisplay(6, "Form VI", "تَفَاعَلَ", "يَتَفَاعَلُ", "تَفَاعُل", "Mutual cooperation, reciprocity, or simulation.", "تَعَاوَنَ (They cooperated)"),
    VerbFormDisplay(7, "Form VII", "انْفَعَلَ", "يَنْفَعِلُ", "انْفِعَال", "Passive or reflexive of Form I; involuntary action.", "انْقَلَبَ (He turned)"),
    VerbFormDisplay(8, "Form VIII", "افْتَعَلَ", "يَفْتَعِلُ", "افْتِعَال", "Reflexive, earnest endeavor, or middle voice.", "اكْتَسَبَ (He earned)"),
    VerbFormDisplay(9, "Form IX", "افْعَلَّ", "يَفْعَلُّ", "افْعِلَال", "Acquiring a color or physical defect.", "اصْفَرَّ (It turned yellow)"),
    VerbFormDisplay(10, "Form X", "اسْتَفْعَلَ", "يَسْتَفْعِلُ", "اسْتِفْعَال", "Seeking, requesting, or deeming an action.", "اسْتَغْفَرَ (He sought forgiveness)"),
)

@Composable
fun MorphologyLabView() {
    var searchRoot by remember { mutableStateOf("") }
    var selectedTab by remember { mutableStateOf(0) } // 0: 10 Verb Forms, 1: Clitic Analyzer

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
                title = "Sarf Lab",
                subtitle = "CLASSICAL ARABIC MORPHOLOGY",
                arabicTitle = "مُخْتَبَر الصَّرْف",
            )
        }

        // 2. Segmented Mode Switch
        item {
            AppleSegmentedControl(
                items = listOf("Verb Forms (الأوزان)", "Clitic Anatomy (اللواصق)"),
                selectedIndex = selectedTab,
                onIndexSelected = { selectedTab = it },
            )
        }

        if (selectedTab == 0) {
            // Intro Inset Card
            item {
                AppleInsetCard {
                    Text(
                        text = "THE 10 DERIVED VERB FORMS",
                        style = MaterialTheme.typography.labelSmall,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.primary,
                        letterSpacing = 1.sp,
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        text = "All Classical Arabic verbs derive from tri-literal roots through 10 standard morphological templates (Awzan / الأوزان).",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }

            // Forms List
            items(sampleForms, key = { it.formNumber }) { form ->
                AppleInsetCard {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Surface(
                                shape = RoundedCornerShape(10.dp),
                                color = MaterialTheme.colorScheme.primaryContainer,
                            ) {
                                Text(
                                    text = "Form ${form.formNumber}",
                                    modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                                    style = MaterialTheme.typography.labelMedium,
                                    fontWeight = FontWeight.Bold,
                                    color = MaterialTheme.colorScheme.primary,
                                )
                            }
                            Spacer(modifier = Modifier.width(10.dp))
                            Text(
                                text = "${form.patternPast} / ${form.patternPresent}",
                                fontSize = 20.sp,
                                fontWeight = FontWeight.Bold,
                                color = MaterialTheme.colorScheme.onSurface,
                            )
                        }

                        ApplePillBadge(
                            text = form.verbalNoun,
                            backgroundColor = MaterialTheme.colorScheme.secondaryContainer,
                            textColor = MaterialTheme.colorScheme.secondary,
                        )
                    }

                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        text = form.description,
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurface,
                    )
                    Spacer(modifier = Modifier.height(6.dp))
                    Text(
                        text = "Quranic Example: ${form.example}",
                        style = MaterialTheme.typography.bodySmall,
                        fontWeight = FontWeight.SemiBold,
                        color = AppleGold,
                    )
                }
            }
        } else {
            // Clitic Anatomy Card
            item {
                AppleInsetCard {
                    Text(
                        text = "QURANIC TOKEN ANATOMY",
                        style = MaterialTheme.typography.labelSmall,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.primary,
                        letterSpacing = 1.sp,
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        text = "Classical Arabic words frequently fuse proclitics (conjunctions, prepositions, articles), a root stem, and enclitic pronouns into a single written token.",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                    Spacer(modifier = Modifier.height(16.dp))

                    // Example Token Decomposition: فَسَيَكْفِيكَهُمُ
                    Surface(
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(16.dp),
                        color = MaterialTheme.colorScheme.surfaceVariant,
                    ) {
                        Column(
                            modifier = Modifier.padding(16.dp),
                            horizontalAlignment = Alignment.CenterHorizontally,
                        ) {
                            Text(
                                text = "فَسَيَكْفِيكَهُمُ",
                                fontSize = 34.sp,
                                fontWeight = FontWeight.Bold,
                                color = MaterialTheme.colorScheme.primary,
                            )
                            Text(
                                text = "Surah Al-Baqarah 2:137",
                                style = MaterialTheme.typography.labelSmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                            )
                            Spacer(modifier = Modifier.height(14.dp))

                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceEvenly,
                            ) {
                                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                    Text("فَـ", fontSize = 22.sp, fontWeight = FontWeight.Bold)
                                    Text("So (Conj)", style = MaterialTheme.typography.labelSmall)
                                }
                                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                    Text("سَـ", fontSize = 22.sp, fontWeight = FontWeight.Bold)
                                    Text("Will (Fut)", style = MaterialTheme.typography.labelSmall)
                                }
                                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                    Text("يَكْفِي", fontSize = 22.sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.primary)
                                    Text("Suffice (Stem)", style = MaterialTheme.typography.labelSmall, fontWeight = FontWeight.Bold)
                                }
                                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                    Text("ـكَ", fontSize = 22.sp, fontWeight = FontWeight.Bold)
                                    Text("You (Obj)", style = MaterialTheme.typography.labelSmall)
                                }
                                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                    Text("ـهُمُ", fontSize = 22.sp, fontWeight = FontWeight.Bold)
                                    Text("Them (Obj)", style = MaterialTheme.typography.labelSmall)
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
