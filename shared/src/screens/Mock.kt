package com.meher.jawhar.screens

class AyahItem(val number: Int, val words: List<String>, val translit: String, val english: String)
class SurahItem(val number: Int, val name: String, val meta: String, val arabic: String)
class DeckItem(val title: String, val sub: String, val progress: Float, val due: String)
class LeaderRow(val rank: Int, val name: String, val initials: String, val xp: String)
class BadgeItem(val title: String, val caption: String, val unlocked: Boolean)
class ChatItem(val text: String, val fromUser: Boolean)
class ConjRow(val label: String, val forms: List<String>)
class ExampleItem(val ref: String, val arabic: String)

class PlacementQ(
    val skill: String,
    val prompt: String,
    val word: String?,
    val options: List<String>,
    val answer: Int,
)

class LessonStep(val kicker: String, val title: String, val word: String?, val translit: String?, val tags: List<String>, val body: String)

class LessonQ(val prompt: String, val options: List<String>, val answer: Int, val explain: String)

class Lesson(
    val title: String,
    val subtitle: String,
    val pattern: String,
    val form: String,
    val minutes: Int,
    val wordCount: Int,
    val xp: Int,
    val goals: List<String>,
    val steps: List<LessonStep>,
    val quiz: List<LessonQ>,
)

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

    val skills = listOf("Vocabulary", "Sarf", "Nahw")

    val placementQuestions = listOf(
        PlacementQ("Vocabulary", "What does the root ك-ت-b carry?", null,
            listOf("writing", "knowledge", "movement", "speech"), 0),
        PlacementQ("Vocabulary", "What does صَلَاةٌ mean?", null,
            listOf("prayer", "praise", "fasting", "pilgrimage"), 0),
        PlacementQ("Vocabulary", "What does عَذَابٌ mean?", null,
            listOf("punishment", "reward", "forgiveness", "mercy"), 0),
        PlacementQ("Vocabulary", "What does the root ن-ص-r carry?", null,
            listOf("help and support", "writing", "movement", "light"), 0),
        PlacementQ("Sarf", "Which word follows the pattern فَاعِلٌ?", "كَاتِبٌ",
            listOf("كَاتِبٌ", "مَكْتُوبٌ", "كِتَابٌ", "مَكْتَبٌ"), 0),
        PlacementQ("Sarf", "Which word follows the pattern مَفْعُولٌ?", null,
            listOf("سَامِعٌ", "مَكْتُوبٌ", "كِتَابٌ", "كَاتِبٌ"), 1),
        PlacementQ("Sarf", "Which is Form IV of the root د-ر-س (يَفْعُلُ)?", null,
            listOf("دَرَسَ", "دَرَّسَ", "دُرُسَ", "أَدْرَسَ"), 0),
        PlacementQ("Sarf", "What is the verbal noun (المصدر) of كَتَبَ?", null,
            listOf("كِتَابٌ", "كِتَابَةٌ", "كَاتِبٌ", "مَكْتُوبٌ"), 1),
        PlacementQ("Nahw", "In «ذَهَبَ الطَّالِبُ», what is الطَّالِبُ?", null,
            listOf("the doer's subject, in the nominative", "the object, in the accusative", "in the genitive", "an adjective"), 0),
        PlacementQ("Nahw", "In «ذَهَبْتُ إلى المدرسةِ», what is المدرسةِ?", null,
            listOf("in the nominative", "in the accusative", "in the genitive", "a conjunction"), 2),
        PlacementQ("Nahw", "An Arabic verb is grammatically always…", null,
            listOf("in the nominative", "in the accusative", "in the genitive", "unmarked"), 1),
        PlacementQ("Nahw", "In «كانَ الطالبُ مجتهدًا», what is مجتهدًا?", null,
            listOf("the subject of كان", "the predicate of كان, in the accusative", "in the genitive", "an emphatic particle"), 1),
    )

    fun placementScore(picks: List<Int?>): Map<String, Float> =
        skills.associateWith { skill ->
            val qs = placementQuestions.withIndex().filter { it.value.skill == skill }
            if (qs.isEmpty()) 0f
            else qs.count { picks.getOrNull(it.index) == it.value.answer }.toFloat() / qs.size
        }

    val lessonFormI = Lesson(
        title = "Form I: Fa'ala",
        subtitle = "The simplest verb pattern, and the base for most Quranic verbs.",
        pattern = "فَعَلَ",
        form = "Form I",
        minutes = 8,
        wordCount = 12,
        xp = 60,
        goals = listOf(
            "Build a past tense verb from a root",
            "Spot Form I in the Quran",
            "Conjugate for he, she and they",
        ),
        steps = listOf(
            LessonStep(
                "CONCEPT", "The past tense pattern", "كَتَبَ", "kataba · he wrote",
                listOf("Root · ك ت ب", "Pattern · فَعَلَ"),
                "Put the three root letters on the pattern فَعَلَ. Each letter takes a fatha, which gives you the plain past tense for he.",
            ),
            LessonStep(
                "CONCEPT", "Start with the root", "ك ت ب", "k-t-b",
                listOf("Three letters", "Carries writing"),
                "A root is three consonants that share one core meaning. Put them on their own first: ك ت ب. The pattern decides what happens next.",
            ),
            LessonStep(
                "CONCEPT", "One fatha per letter", "كَتَبَ", "kataba · he wrote",
                listOf("ك + fatha", "ت + fatha", "ب + fatha"),
                "Form I gives every letter the same short vowel. Because nothing is doubled or shortened, Form I is the pattern you will meet most often.",
            ),
            LessonStep(
                "CONCEPT", "The vowel carries meaning", "كَتَبَ", "kataba · he wrote",
                listOf("فَعَلَ", "vs فَعِلَ", "vs فَعُلَ"),
                "Change one vowel and you change the meaning. The same root on a different pattern gives a different verb, so the pattern is what tells you which one you are reading.",
            ),
            LessonStep(
                "CONCEPT", "Spotting it in text", "كَتَبَ", "kataba · he wrote",
                listOf("Three consonants", "Three fathas", "No doubling"),
                "Scan a word for three consonants in a row carrying three plain fathas. If nothing is doubled, shortened or prefixed, you are almost certainly looking at Form I.",
            ),
        ),
        quiz = listOf(
            LessonQ(
                "Which word is Form I past of the root ك-ت-b?",
                listOf("كَتَبَ", "كَتَّبَ", "كُتُبَ", "كَاتَبَ"), 0,
                "كَتَبَ is the root ك-ت-b on فَعَلَ with a fatha on each letter. كَتَّبَ doubles the middle letter, which is Form II.",
            ),
            LessonQ(
                "How many letters does a triliteral root like ك-ت-b have?",
                listOf("One", "Two", "Three", "Four"), 2,
                "Arabic roots are built from three consonants. That is why they are called triliteral.",
            ),
            LessonQ(
                "Form II doubles the middle letter's vowel. What does that give you from ك-ت-b?",
                listOf("دَرَسَ", "كَتَّبَ", "أَدْرَسَ", "كَاتَبَ"), 1,
                "Form II follows فَعَّلَ. Doubling the fatha on the middle letter turns كَتَبَ into كَتَّبَ.",
            ),
            LessonQ(
                "Which of these is Form I past of the root د-ر-س?",
                listOf("دَرَسَ", "دَرَّسَ", "دُرُسَ", "أَدْرَسَ"), 0,
                "Form IV on the pattern أَفْعَلَ gives أَدْرَسَ, and Form II gives دَرَّسَ. Only دَرَسَ keeps the plain Form I shape.",
            ),
            LessonQ(
                "In a Form I past verb like كَتَبَ, how many fathas does the root carry?",
                listOf("One", "Two", "Three", "None"), 2,
                "Form I gives each of the three letters a fatha, so كَتَبَ carries three.",
            ),
        ),
    )

    fun lessonScore(quiz: List<LessonQ>, picks: List<Int?>): Float =
        if (quiz.isEmpty()) 0f else quiz.withIndex().count { (i, q) -> picks.getOrNull(i) == q.answer }.toFloat() / quiz.size
}
