package com.meher.jawhar.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import com.meher.jawhar.design.*
import com.meher.jawhar.nav.JNav

@Composable
fun GalleryPanel(nav: JNav, modifier: Modifier = Modifier) {
    val c = Jawhar.colors
    val t = Jawhar.type
    LazyColumn(modifier.background(c.bgSurface).padding(horizontal = 16.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
        item {
            JText("Jawhar UI catalog", t.titleL, c.onSurface, Modifier.padding(top = 24.dp))
            JText("${Screens.all.size} screens. Click one to preview it.", t.bodyS, c.onSurfaceVariant, Modifier.padding(bottom = 12.dp))
        }
        Screens.all.groupBy { it.group }.forEach { (group, specs) ->
            item { JSectionLabel(group, Modifier.padding(top = 14.dp, bottom = 4.dp)) }
            items(specs) { s ->
                val on = nav.current == s.id
                Row(
                    Modifier.fillMaxWidth().clip(SquircleShape(14.dp)).background(if (on) c.primaryContainer else Color.Transparent).tappable { nav.reset(s.id) }.padding(horizontal = 12.dp, vertical = 9.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    JText(s.title, t.bodyM, if (on) c.onPrimaryContainer else c.onSurface)
                }
            }
        }
    }
}
