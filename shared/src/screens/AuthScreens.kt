package com.meher.jawhar.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.meher.jawhar.data.LocalApi
import com.meher.jawhar.data.api.AuthApi
import com.meher.jawhar.design.*
import com.meher.jawhar.nav.Dest
import com.meher.jawhar.nav.LocalNav

@Composable
fun SplashScreen() {
    val c = Jawhar.colors
    val nav = LocalNav.current
    Box(
        Modifier
            .fillMaxSize()
            .background(c.bgInverse)
            .starOrnaments(c.accent, StarSpec(40.dp, 60.dp, 480.dp, 0.2f), StarSpec(380.dp, 800.dp, 460.dp, 0.15f), StarSpec(195.dp, 370.dp, 330.dp, 0.13f))
            .tappable { nav.go(Dest.Welcome1) },
        contentAlignment = Alignment.Center,
    ) {
        Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(12.dp)) {
            JLogoMark(size = 116.dp)
            Spacer(Modifier.height(8.dp))
            JText("Jawhar", Jawhar.type.displayL, c.onInverse)
            JArabic("افهم القرآن بلغته", Jawhar.type.arabicHeading, c.accent)
        }
        JText(
            "Classical Arabic · Sarf · Nahw",
            Jawhar.type.labelM,
            c.onInverse.copy(alpha = 0.6f),
            Modifier.align(Alignment.BottomCenter).padding(bottom = 64.dp),
        )
    }
}

@Composable
fun WelcomeScreen(page: Int) {
    val c = Jawhar.colors
    val nav = LocalNav.current
    val top = LocalTopInset.current
    val tone = when (page) { 0 -> c.primaryContainer; 1 -> c.accentContainer; else -> c.infoContainer }
    val starTint = when (page) { 0 -> c.primary; 1 -> c.accent; else -> c.info }
    val title = when (page) {
        0 -> "Understand the Quran in its own language"
        1 -> "Roots, patterns and grammar made visible"
        else -> "A tutor that explains, quizzes and remembers"
    }
    val body = when (page) {
        0 -> "Go beyond translation. Learn how every word is built, so you can read the meaning directly."
        1 -> "Sarf shows how words are formed. Nahw shows how they connect. Both, in colour."
        else -> "Ask anything about an ayah. Review words at the perfect moment so they stay."
    }
    val next = when (page) { 0 -> Dest.Welcome2; 1 -> Dest.Welcome3; else -> Dest.GetStarted }
    Page(
        back = false,
        cta = { JButton(if (page == 2) "Get started" else "Continue", { nav.go(next) }) },
        overlay = {
            JGlassPill("Skip", Modifier.align(Alignment.TopEnd).padding(top = top + 10.dp, end = 24.dp).tappable { nav.go(Dest.GetStarted) })
        },
    ) {
        Box(
            Modifier
                .fillMaxWidth()
                .height(400.dp)
                .clip(SquircleShape(52.dp))
                .background(tone)
                .starOrnaments(starTint, StarSpec(160.dp, 200.dp, 440.dp, 0.3f), StarSpec(300.dp, 350.dp, 300.dp, 0.2f)),
            contentAlignment = Alignment.Center,
        ) {
            when (page) {
                0 -> Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    JArabic("فَهِمَ", Jawhar.type.arabicWordXL, c.onPrimaryContainer)
                    JText("fahima · he understood", Jawhar.type.translit, c.onPrimaryContainer.copy(alpha = 0.8f))
                    Spacer(Modifier.height(12.dp))
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        JTag("Root · ف ه م")
                        JTag("Form I")
                    }
                }
                1 -> Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                        listOf("ب", "ت", "ك").forEach { l ->
                            Box(Modifier.size(64.dp).clip(CircleShape).background(c.bgSurface), contentAlignment = Alignment.Center) {
                                JArabic(l, Jawhar.type.arabicHeading, c.onPrimaryContainer)
                            }
                        }
                    }
                    JText("One root, many words", Jawhar.type.labelL, c.onAccentContainer)
                    listOf("كَاتِبٌ" to "writer", "كِتَابٌ" to "book", "مَكْتُوبٌ" to "written").forEach { (ar, en) ->
                        Row(
                            Modifier.padding(horizontal = 26.dp).fillMaxWidth().clip(SquircleShape(24.dp)).background(c.bgSurface).padding(horizontal = 24.dp, vertical = 4.dp),
                            verticalAlignment = Alignment.CenterVertically,
                        ) {
                            JText(en, Jawhar.type.titleS, c.onAccentContainer, Modifier.weight(1f))
                            JArabic(ar, Jawhar.type.arabicHeading, c.onSurface)
                        }
                    }
                }
                else -> Column(Modifier.padding(horizontal = 20.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
                    JChatBubble("The root of ar-Rahman is r-h-m, the idea of mercy.", false)
                    JChatBubble("Quiz me on that root, please.", true)
                    Row(Modifier.fillMaxWidth().padding(top = 14.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        JRating.values().forEach { r ->
                            Box(Modifier.weight(1f).clip(SquircleShape(22.dp)).background(c.bgSurface)) { JRatingButton(r, {}, Modifier.fillMaxWidth()) }
                        }
                    }
                    JText("Spaced repetition keeps it for good", Jawhar.type.labelL, c.onSurfaceVariant, Modifier.fillMaxWidth(), TextAlign.Center)
                }
            }
        }
        JText(title, Jawhar.type.headlineM, c.onSurface, Modifier.padding(top = 8.dp))
        JText(body, Jawhar.type.bodyL, c.onSurfaceVariant)
        PageDots(3, page, Modifier.align(Alignment.CenterHorizontally).padding(top = 8.dp))
    }
}

@Composable
fun GetStartedScreen() {
    val nav = LocalNav.current
    Page(
        back = false,
        cta = {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                JButton("Sign up with email", { nav.go(Dest.SignUp) })
                JButton("Continue with Google", { nav.go(Dest.PlacementIntro) }, style = JButtonStyle.Neutral)
                JButton("I already have an account", { nav.go(Dest.LogIn) }, style = JButtonStyle.Text)
                JText("By continuing you agree to our Terms and Privacy Policy.", Jawhar.type.bodyS, Jawhar.colors.onSurfaceSubtle, Modifier.fillMaxWidth(), TextAlign.Center)
            }
        },
    ) {
        Column(Modifier.fillMaxWidth().padding(top = 56.dp), horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(16.dp)) {
            JLogoMark(size = 88.dp)
            Spacer(Modifier.height(8.dp))
            BigTitle("Understand the Quran in its own language", "A free, AI-powered way to learn Classical Arabic grammar.", center = true)
        }
    }
}

@Composable
fun SignUpScreen(validation: Boolean = false) {
    val nav = LocalNav.current
    val api = LocalApi.current
    var name by remember { mutableStateOf("") }
    var email by remember { mutableStateOf(if (validation) "meher@" else "") }
    var password by remember { mutableStateOf("") }
    var agreed by remember { mutableStateOf(!validation) }
    var loading by remember { mutableStateOf(false) }
    var errorMsg by remember { mutableStateOf<String?>(null) }
    var submit by remember { mutableStateOf(false) }

    if (submit) {
        LaunchedEffect(Unit) {
            submit = false
            loading = true
            errorMsg = null
            try {
                AuthApi.register(api, email, name, password)
                nav.go(Dest.Verify)
            } catch (e: Exception) {
                errorMsg = "Could not create account. Check your details and try again."
            } finally {
                loading = false
            }
        }
    }

    Page {
        BigTitle("Create your account", "Start your Arabic journey in a minute.")
        if (errorMsg != null) JBanner(JBannerKind.Error, "Sign up failed", errorMsg!!)
        JTextField(name, { name = it }, "Full name", placeholder = "Meher Ali", trailing = JI.User)
        JTextField(email, { email = it }, "Email", placeholder = "you@example.com",
            helper = if (validation && email.isNotBlank() && !email.contains("@")) "Enter a valid email address" else null,
            isError = validation && !email.contains("@"), trailing = JI.Mail)
        JTextField(password, { password = it }, "Password", placeholder = "Minimum 8 characters", password = true)
        CheckRow(agreed, { agreed = it }, "I agree to the Terms and Privacy Policy")
        JButton("Create account", { submit = true },
            enabled = !loading && name.isNotBlank() && email.contains("@") && password.length >= 8 && agreed)
        OrDivider()
        JButton("Continue with Google", { nav.go(Dest.PlacementIntro) }, style = JButtonStyle.Neutral)
        FooterLink("Already have an account?", "Log in") { nav.go(Dest.LogIn) }
    }
}

@Composable
fun LogInScreen(error: Boolean = false) {
    val nav = LocalNav.current
    val api = LocalApi.current
    var email by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var loading by remember { mutableStateOf(false) }
    var failed by remember { mutableStateOf(error) }
    var submit by remember { mutableStateOf(false) }

    if (submit) {
        LaunchedEffect(Unit) {
            submit = false
            loading = true
            failed = false
            try {
                AuthApi.login(api, email, password)
                nav.reset(Dest.Home)
            } catch (e: Exception) {
                failed = true
            } finally {
                loading = false
            }
        }
    }

    Page {
        BigTitle("Welcome back", "Pick up right where you left off.")
        if (failed) JBanner(JBannerKind.Error, "Could not log in", "Check your email and password, then try again.")
        JTextField(email, { email = it }, "Email", placeholder = "you@example.com",
            isError = failed, trailing = JI.Mail)
        JTextField(password, { password = it }, "Password",
            helper = if (failed) "That password is not correct" else null,
            isError = failed, password = true)
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.End) {
            JText("Forgot password?", Jawhar.type.labelL, Jawhar.colors.primary, Modifier.tappable { nav.go(Dest.Forgot) })
        }
        JButton("Log in", { submit = true }, enabled = !loading && email.isNotBlank() && password.isNotBlank())
        OrDivider()
        JButton("Continue with Google", { nav.reset(Dest.Home) }, style = JButtonStyle.Neutral)
        FooterLink("New here?", "Create an account") { nav.go(Dest.SignUp) }
    }
}

@Composable
fun ForgotPasswordScreen() {
    val nav = LocalNav.current
    Page {
        CircleIcon(JI.Lock, Jawhar.colors.primaryContainer, Jawhar.colors.onPrimaryContainer)
        BigTitle("Forgot your password?", "Enter the email you signed up with and we will send a reset link.")
        StatefulField("Email", "", "you@example.com", trailing = JI.Mail)
        JButton("Send reset link", { nav.go(Dest.LogIn) })
        JButton("Back to log in", { nav.back() }, style = JButtonStyle.Text)
    }
}

@Composable
fun ResetSentScreen() {
    val nav = LocalNav.current
    StateScreen(
        icon = JI.Mail,
        tile = Jawhar.colors.primaryContainer,
        tint = Jawhar.colors.primary,
        title = "Check your inbox",
        body = "We sent a reset link to meher@email.com. It expires in 30 minutes.",
        primary = "Open email app",
        secondary = "Resend link",
        back = true,
        onSecondary = {},
        onPrimary = { nav.go(Dest.LogIn) },
    )
}

@Composable
fun VerifyEmailScreen() {
    val nav = LocalNav.current
    val c = Jawhar.colors
    var code by remember { mutableStateOf("482") }
    Page {
        BigTitle("Check your email", "We sent a 6 digit code to meher@email.com")
        BasicTextField(
            value = code,
            onValueChange = { if (it.length <= 6 && it.all { ch -> ch.isDigit() }) code = it },
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.NumberPassword),
            cursorBrush = SolidColor(c.primary),
            textStyle = Jawhar.type.headlineS.copy(color = c.onSurface),
            modifier = Modifier.fillMaxWidth().padding(top = 16.dp),
            decorationBox = {
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    repeat(6) { i ->
                        Box(
                            Modifier.size(48.dp, 56.dp).clip(SquircleShape(16.dp)).background(if (i == code.length) c.primaryContainer else c.bgSurfaceVariant),
                            contentAlignment = Alignment.Center,
                        ) {
                            if (i < code.length) JText(code[i].toString(), Jawhar.type.headlineS, c.onSurface)
                        }
                    }
                }
            },
        )
        JText("Resend code in 0:42", Jawhar.type.labelL, c.onSurfaceVariant, Modifier.fillMaxWidth(), TextAlign.Center)
        JButton("Verify", { nav.go(Dest.PlacementIntro) }, enabled = code.length == 6)
        JButton("Change email", { nav.back() }, style = JButtonStyle.Text)
    }
}
