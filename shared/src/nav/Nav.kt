package com.meher.jawhar.nav

import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.staticCompositionLocalOf
import com.meher.jawhar.design.JTab

class JNav(start: String) {
    val stack = mutableStateListOf(start)
    var isForward: Boolean = true
        private set
    var isTabSwitch: Boolean = false
        private set

    val current: String get() = stack.last()
    val canGoBack: Boolean get() = stack.size > 1

    fun go(id: String) {
        isForward = true
        isTabSwitch = false
        stack.add(id)
    }

    fun back() {
        if (stack.size > 1) {
            isForward = false
            isTabSwitch = false
            stack.removeAt(stack.lastIndex)
        }
    }

    fun reset(id: String) {
        isForward = true
        isTabSwitch = false
        stack.clear()
        stack.add(id)
    }

    fun tab(tab: JTab) {
        val target = when (tab) {
            JTab.Home -> Dest.Home
            JTab.Learn -> Dest.Learn
            JTab.Quran -> Dest.Quran
            JTab.Tutor -> Dest.TutorStart
            JTab.Profile -> Dest.Profile
        }
        if (current == target) return
        isForward = true
        isTabSwitch = true
        stack.clear()
        stack.add(target)
    }
}

val LocalNav = staticCompositionLocalOf { JNav(Dest.Splash) }

object Dest {
    const val Splash = "splash"
    const val Welcome1 = "welcome1"
    const val Welcome2 = "welcome2"
    const val Welcome3 = "welcome3"
    const val GetStarted = "getStarted"
    const val SignUp = "signUp"
    const val LogIn = "logIn"
    const val Forgot = "forgot"
    const val Verify = "verify"
    const val PlacementIntro = "placementIntro"
    const val PlacementQuestion = "placementQuestion"
    const val PlacementResult = "placementResult"
    const val DailyGoal = "dailyGoal"
    const val NotifPermission = "notifPermission"
    const val Home = "home"
    const val Learn = "learn"
    const val Quran = "quran"
    const val TutorStart = "tutorStart"
    const val Profile = "profile"
    const val LessonIntro = "lessonIntro"
    const val LessonContent = "lessonContent"
    const val LessonQuiz = "lessonQuiz"
    const val LessonComplete = "lessonComplete"
    const val DailyChallenge = "dailyChallenge"
    const val Reader = "reader"
    const val Sarf = "sarf"
    const val WordFamily = "wordFamily"
    const val Conjugation = "conjugation"
    const val NahwInput = "nahwInput"
    const val NahwResult = "nahwResult"
    const val Search = "search"
    const val TutorChat = "tutorChat"
    const val TutorHistory = "tutorHistory"
    const val FlashFront = "flashFront"
    const val FlashBack = "flashBack"
    const val ReviewDone = "reviewDone"
    const val Vocab = "vocab"
    const val Progress = "progress"
    const val Leaderboard = "leaderboard"
    const val Badges = "badges"
    const val EditProfile = "editProfile"
    const val Settings = "settings"
    const val Appearance = "appearance"
    const val NotifSettings = "notifSettings"
    const val Help = "help"

    val TabDestinations = setOf(Home, Learn, Quran, TutorStart, Profile)
}
