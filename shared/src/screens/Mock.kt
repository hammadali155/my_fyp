package com.meher.jawhar.screens

class AyahItem(val number: Int, val words: List<String>, val translit: String, val english: String)
class SurahItem(val number: Int, val name: String, val meta: String, val arabic: String)
class DeckItem(val title: String, val sub: String, val progress: Float, val due: String)
class LeaderRow(val rank: Int, val name: String, val initials: String, val xp: String)
class BadgeItem(val title: String, val caption: String, val unlocked: Boolean)
class ChatItem(val text: String, val fromUser: Boolean)
class ConjRow(val label: String, val forms: List<String>)
class ExampleItem(val ref: String, val arabic: String)

object Mock {
    val ayat = listOf(
        AyahItem(1, listOf("بِسْمِ", "ٱللَّهِ", "ٱلرَّحْمَٰنِ", "ٱلرَّحِيمِ"), "Bismillāhir-raḥmānir-raḥīm", "In the name of God, the Most Gracious, the Most Merciful."),
        AyahItem(2, listOf("ٱلْحَمْدُ", "لِلَّهِ", "رَبِّ", "ٱلْعَٰلَمِينَ"), "Al-ḥamdu lillāhi rabbil-’ālamīn", "Praise belongs to God, Lord of all the worlds."),
        AyahItem(3, listOf("ٱلرَّحْمَٰنِ", "ٱلرَّحِيمِ"), "Ar-raḥmānir-raḥīm", "The Most Gracious, the Most Merciful."),
    )

    val surahs = listOf(
        SurahItem(1, "Al-Fatiha", "The Opening · 7 ayat · Meccan", "الفاتحة"),
        SurahItem(2, "Al-Baqarah", "The Cow · 286 ayat · Medinan", "البقرة"),
        SurahItem(3, "Ali 'Imran", "The Family of Imran · 200 ayat", "آل عمران"),
        SurahItem(4, "An-Nisa", "The Women · 176 ayat · Medinan", "النساء"),
        SurahItem(5, "Al-Ma'idah", "The Table Spread · 120 ayat", "المائدة"),
    )

    val decks = listOf(
        DeckItem("Top 100 Quranic words", "62 of 100 learned", 0.62f, "15 due"),
        DeckItem("Common verbs", "34 of 80 learned", 0.42f, "6 due"),
        DeckItem("Names of God", "12 of 99 learned", 0.12f, "3 due"),
        DeckItem("Prepositions", "18 of 20 learned", 0.9f, "Done"),
    )

    val leaders = listOf(
        LeaderRow(4, "Ayesha M.", "AM", "2,680 XP"),
        LeaderRow(5, "Usman T.", "UT", "2,610 XP"),
        LeaderRow(6, "Zainab H.", "ZH", "2,540 XP"),
        LeaderRow(7, "Omar S.", "OS", "2,490 XP"),
    )

    val badges = listOf(
        BadgeItem("Root Seeker", "Analyse 50 roots", true),
        BadgeItem("7 Day Streak", "7 days in a row", true),
        BadgeItem("First Lesson", "Finish a lesson", true),
        BadgeItem("Word Smith", "Learn 500 words", false),
        BadgeItem("30 Day Streak", "Study 30 days", false),
        BadgeItem("Parser Pro", "Parse 100 verses", false),
        BadgeItem("Night Owl", "After 10 PM", true),
        BadgeItem("Quiz Whiz", "10 perfect quizzes", false),
        BadgeItem("Top Ten", "Weekly top 10", false),
        BadgeItem("Early Bird", "Before 7 AM", false),
        BadgeItem("Tutor Fan", "Ask 25 questions", true),
        BadgeItem("Collector", "Bookmark 20 ayat", false),
    )

    val chat = listOf(
        ChatItem("Can you explain the root of الرَّحْمَٰن?", true),
        ChatItem("Of course. The root is ر ح م, which carries the idea of mercy. Several words in Al-Fatiha come from it.", false),
    )

    val conjugation = listOf(
        ConjRow("3rd m.", listOf("كَتَبَ", "كَتَبَا", "كَتَبُوا")),
        ConjRow("3rd f.", listOf("كَتَبَتْ", "كَتَبَتَا", "كَتَبْنَ")),
        ConjRow("2nd m.", listOf("كَتَبْتَ", "كَتَبْتُمَا", "كَتَبْتُمْ")),
        ConjRow("2nd f.", listOf("كَتَبْتِ", "كَتَبْتُمَا", "كَتَبْتُنَّ")),
        ConjRow("1st", listOf("كَتَبْتُ", "—", "كَتَبْنَا")),
    )

    val examples = listOf(
        ExampleItem("Al-Fatiha 1:2", "ٱلْحَمْدُ لِلَّهِ رَبِّ ٱلْعَٰلَمِينَ"),
        ExampleItem("Al-Ikhlas 112:1", "قُلْ هُوَ ٱللَّهُ أَحَدٌ"),
        ExampleItem("Al-Baqarah 2:255", "ٱللَّهُ لَآ إِلَٰهَ إِلَّا هُوَ"),
    )

    val weekMinutes = listOf(8, 12, 0, 10, 15, 6, 0)
    val weekDays = listOf("M", "T", "W", "T", "F", "S", "S")
}
