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
import androidx.compose.foundation.layout.width
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
import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.runtime.rememberCoroutineScope
import kotlinx.coroutines.launch
import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.core.CubicBezierEasing
import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.slideInVertically
import androidx.compose.animation.slideOutVertically
import androidx.compose.animation.togetherWith
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.graphics.PathEffect
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.rotate
import androidx.compose.ui.graphics.graphicsLayer
import com.meher.jawhar.data.LocalApi
import com.meher.jawhar.data.api.AuthApi
import com.meher.jawhar.design.*
import com.meher.jawhar.nav.Dest
import com.meher.jawhar.nav.LocalNav

@Composable
fun SplashScreen() {
    val c = Jawhar.colors
    val nav = LocalNav.current

    LaunchedEffect(Unit) {
        kotlinx.coroutines.delay(100)
        if (com.meher.jawhar.data.AppState.isLoggedIn()) {
            nav.reset(Dest.Home)
        } else {
            nav.go(Dest.Welcome1)
        }
    }

    Box(
        Modifier
            .fillMaxSize()
            .background(c.bgInverse)
            .starOrnaments(c.accent, StarSpec(40.dp, 60.dp, 480.dp, 0.2f), StarSpec(380.dp, 800.dp, 460.dp, 0.15f), StarSpec(195.dp, 370.dp, 330.dp, 0.13f))
            .tappable {
                if (com.meher.jawhar.data.AppState.isLoggedIn()) {
                    nav.reset(Dest.Home)
                } else {
                    nav.go(Dest.Welcome1)
                }
            },
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

@OptIn(ExperimentalFoundationApi::class)
@Composable
fun WelcomeScreen(page: Int = 0) {
    val c = Jawhar.colors
    val nav = LocalNav.current
    val top = LocalTopInset.current
    val scope = rememberCoroutineScope()
    val pagerState = rememberPagerState(initialPage = page.coerceIn(0, 2)) { 3 }
    val currentPage = pagerState.currentPage
    val isLast = currentPage == 2
    val isFirst = currentPage == 0

    val infiniteTransition = rememberInfiniteTransition(label = "welcome_orbit")
    val orbitRotation by infiniteTransition.animateFloat(
        initialValue = 0f,
        targetValue = 360f,
        animationSpec = infiniteRepeatable(
            animation = tween(26000, easing = LinearEasing),
            repeatMode = RepeatMode.Restart,
        ),
        label = "orbit_rot",
    )
    val floatY by infiniteTransition.animateFloat(
        initialValue = -3f,
        targetValue = 3f,
        animationSpec = infiniteRepeatable(
            animation = tween(2200, easing = CubicBezierEasing(0.4f, 0f, 0.6f, 1f)),
            repeatMode = RepeatMode.Reverse,
        ),
        label = "float_y",
    )
    val pulse by infiniteTransition.animateFloat(
        initialValue = 0.94f,
        targetValue = 1.06f,
        animationSpec = infiniteRepeatable(
            animation = tween(1800, easing = CubicBezierEasing(0.4f, 0f, 0.6f, 1f)),
            repeatMode = RepeatMode.Reverse,
        ),
        label = "pulse",
    )

    val targetTone = when (currentPage) {
        0 -> c.primaryContainer
        1 -> c.accentContainer
        else -> c.infoContainer
    }
    val animatedCardBg by androidx.compose.animation.animateColorAsState(
        targetValue = targetTone,
        animationSpec = tween(380, easing = CubicBezierEasing(0.25f, 0.1f, 0.25f, 1f)),
        label = "card_bg",
    )
    val targetStar = when (currentPage) {
        0 -> c.primary
        1 -> c.accent
        else -> c.info
    }
    val animatedStar by androidx.compose.animation.animateColorAsState(
        targetValue = targetStar,
        animationSpec = tween(380, easing = CubicBezierEasing(0.25f, 0.1f, 0.25f, 1f)),
        label = "star_tint",
    )

    val titles = listOf(
        "Understand the Quran in its own language",
        "Roots, patterns and grammar made visible",
        "A tutor that explains, quizzes and remembers",
    )
    val bodies = listOf(
        "Go beyond translation. Learn how every word is built, so you can read the meaning directly.",
        "Sarf shows how words are formed. Nahw shows how they connect. Both, in colour.",
        "Ask anything about an ayah. Review words at the perfect moment so they stay.",
    )

    val skipAlpha by androidx.compose.animation.core.animateFloatAsState(
        targetValue = if (isLast) 0f else 1f,
        animationSpec = tween(260, easing = CubicBezierEasing(0.25f, 0.1f, 0.25f, 1f)),
        label = "skip_alpha",
    )

    val backWeight by androidx.compose.animation.core.animateFloatAsState(
        targetValue = if (isFirst || isLast) 0f else 1f,
        animationSpec = tween(320, easing = CubicBezierEasing(0.25f, 0.1f, 0.25f, 1f)),
        label = "back_weight",
    )

    Page(
        back = false,
        scroll = false,
        cta = {
            Row(
                Modifier.fillMaxWidth().height(52.dp),
                horizontalArrangement = Arrangement.spacedBy(if (backWeight > 0.01f) 10.dp else 0.dp),
            ) {
                if (backWeight > 0.01f) {
                    Box(Modifier.weight(backWeight).graphicsLayer { alpha = backWeight }) {
                        JButton(
                            "Back",
                            onClick = {
                                scope.launch {
                                    pagerState.animateScrollToPage(currentPage - 1)
                                }
                            },
                            modifier = Modifier.fillMaxWidth(),
                            style = JButtonStyle.Tonal,
                        )
                    }
                }
                Box(Modifier.weight(1f)) {
                    JButton(
                        text = if (isLast) "Get started" else "Next",
                        onClick = {
                            if (currentPage < 2) {
                                scope.launch {
                                    pagerState.animateScrollToPage(currentPage + 1)
                                }
                            } else {
                                nav.go(Dest.GetStarted)
                            }
                        },
                        modifier = Modifier.fillMaxWidth(),
                        style = if (isLast) JButtonStyle.Accent else JButtonStyle.Filled,
                    )
                }
            }
        },
        overlay = {
            if (skipAlpha > 0.01f) {
                JGlassPill(
                    "Skip",
                    Modifier
                        .align(Alignment.TopEnd)
                        .padding(top = top + 10.dp, end = 24.dp)
                        .graphicsLayer { alpha = skipAlpha }
                        .tappable(enabled = !isLast) { nav.go(Dest.GetStarted) },
                )
            }
        },
    ) {
        Box(
            Modifier
                .fillMaxWidth()
                .height(360.dp)
                .clip(SquircleShape(48.dp))
                .background(animatedCardBg)
                .starOrnaments(
                    animatedStar,
                    StarSpec(160.dp, 200.dp, 440.dp, 0.28f),
                    StarSpec(300.dp, 350.dp, 300.dp, 0.18f),
                )
                .drawBehind {
                    rotate(orbitRotation) {
                        drawCircle(
                            color = animatedStar.copy(alpha = 0.14f),
                            radius = size.minDimension * 0.44f,
                            style = Stroke(
                                width = 1.5.dp.toPx(),
                                pathEffect = PathEffect.dashPathEffect(floatArrayOf(14f, 18f), 0f),
                            ),
                        )
                        drawCircle(
                            color = animatedStar.copy(alpha = 0.08f),
                            radius = size.minDimension * 0.58f,
                            style = Stroke(
                                width = 1.dp.toPx(),
                                pathEffect = PathEffect.dashPathEffect(floatArrayOf(24f, 28f), 0f),
                            ),
                        )
                    }
                },
            contentAlignment = Alignment.Center,
        ) {
            HorizontalPager(
                state = pagerState,
                modifier = Modifier.fillMaxSize(),
            ) { p ->
                Box(
                    Modifier.fillMaxSize().padding(horizontal = 20.dp),
                    contentAlignment = Alignment.Center,
                ) {
                    when (p) {
                        0 -> WelcomeSceneQuran(floatY, pulse)
                        1 -> WelcomeSceneMorphology(floatY)
                        else -> WelcomeSceneAiTutor(pulse)
                    }
                }
            }
        }
        PageDots(3, currentPage, Modifier.align(Alignment.CenterHorizontally).padding(top = 10.dp))
        Box(
            Modifier.fillMaxWidth().height(56.dp),
            contentAlignment = Alignment.CenterStart,
        ) {
            AnimatedContent(
                targetState = currentPage,
                transitionSpec = {
                    (fadeIn(tween(220)) + slideInVertically(tween(220)) { h -> h / 3 }) togetherWith
                        (fadeOut(tween(160)) + slideOutVertically(tween(160)) { h -> -h / 3 })
                },
                label = "welcome_title",
            ) { idx ->
                JText(titles[idx], Jawhar.type.headlineM, c.onSurface, maxLines = 2)
            }
        }
        Box(
            Modifier.fillMaxWidth().height(44.dp),
            contentAlignment = Alignment.CenterStart,
        ) {
            AnimatedContent(
                targetState = currentPage,
                transitionSpec = {
                    (fadeIn(tween(220)) + slideInVertically(tween(220)) { h -> h / 3 }) togetherWith
                        (fadeOut(tween(160)) + slideOutVertically(tween(160)) { h -> -h / 3 })
                },
                label = "welcome_body",
            ) { idx ->
                JText(bodies[idx], Jawhar.type.bodyL, c.onSurfaceVariant, maxLines = 2)
            }
        }
    }
}

@Composable
private fun WelcomeSceneQuran(floatY: Float, pulse: Float) {
    val c = Jawhar.colors
    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(10.dp),
        modifier = Modifier.graphicsLayer { translationY = floatY },
    ) {
        Box(
            Modifier
                .size(80.dp)
                .clip(SquircleShape(24.dp))
                .background(c.bgSurface.copy(alpha = 0.96f))
                .softShadow(SquircleShape(24.dp), 18.dp, 0.22f),
            contentAlignment = Alignment.Center,
        ) {
            JIcon(JI.Quran, size = 40.dp, tint = c.primary, strokeWidth = 1.4.dp)
        }
        Spacer(Modifier.height(2.dp))
        Row(
            Modifier
                .clip(SquircleShape(22.dp))
                .background(c.bgSurface.copy(alpha = 0.9f))
                .padding(horizontal = 18.dp, vertical = 10.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            JArabic("بِسْمِ ٱللَّهِ", Jawhar.type.arabicHeading, c.primary)
        }
        JText("In the name of God", Jawhar.type.translit, c.onPrimaryContainer.copy(alpha = 0.85f))
        Spacer(Modifier.height(2.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            listOf("ب", "س", "م").forEach { letter ->
                Box(
                    Modifier
                        .size(38.dp)
                        .clip(CircleShape)
                        .background(c.primary.copy(alpha = 0.14f))
                        .graphicsLayer {
                            scaleX = pulse
                            scaleY = pulse
                        },
                    contentAlignment = Alignment.Center,
                ) {
                    JArabic(letter, Jawhar.type.arabicWordL, c.primary)
                }
            }
        }
        JText("Tap any word to see its root and meaning", Jawhar.type.labelM, c.onPrimaryContainer.copy(alpha = 0.68f), textAlign = TextAlign.Center)
    }
}

@Composable
private fun WelcomeSceneMorphology(floatY: Float) {
    val c = Jawhar.colors
    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(6.dp),
        modifier = Modifier.fillMaxWidth().graphicsLayer { translationY = floatY * 0.6f },
    ) {
        Box(
            Modifier
                .size(72.dp)
                .clip(CircleShape)
                .background(c.bgSurface.copy(alpha = 0.94f))
                .softShadow(CircleShape, 14.dp, 0.18f),
            contentAlignment = Alignment.Center,
        ) {
            JArabic("ك ت ب", Jawhar.type.arabicHeading, c.accent)
        }
        JText("Root · k-t-b", Jawhar.type.labelM, c.onAccentContainer.copy(alpha = 0.9f))
        Spacer(Modifier.height(2.dp))
        Column(verticalArrangement = Arrangement.spacedBy(5.dp)) {
            listOf(
                Triple("كَتَبَ", "he wrote", c.roleFaail),
                Triple("كِتَابٌ", "book", c.accent),
                Triple("كَاتِبٌ", "writer", c.roleMubtada),
                Triple("مَكْتُوبٌ", "written", c.roleMaful),
            ).forEach { (ar, en, dotColor) ->
                Row(
                    Modifier
                        .fillMaxWidth()
                        .clip(SquircleShape(16.dp))
                        .background(c.bgSurface.copy(alpha = 0.92f))
                        .padding(horizontal = 14.dp, vertical = 7.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Box(Modifier.size(8.dp).clip(CircleShape).background(dotColor))
                    Spacer(Modifier.width(10.dp))
                    JText(en, Jawhar.type.titleS, c.onSurface, Modifier.weight(1f))
                    JArabic(ar, Jawhar.type.arabicWordL, c.onSurface)
                }
            }
        }
    }
}

@Composable
private fun WelcomeSceneAiTutor(pulse: Float) {
    val c = Jawhar.colors
    Column(
        Modifier.fillMaxWidth().padding(horizontal = 4.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Row(
            Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.Center,
        ) {
            Box(
                Modifier
                    .size(52.dp)
                    .clip(CircleShape)
                    .background(c.bgSurface.copy(alpha = 0.92f))
                    .softShadow(CircleShape, 12.dp, 0.18f)
                    .graphicsLayer { scaleX = pulse; scaleY = pulse },
                contentAlignment = Alignment.Center,
            ) {
                JIcon(JI.Spark, size = 26.dp, tint = c.info, strokeWidth = 1.4.dp)
            }
        }
        Spacer(Modifier.height(2.dp))
        JChatBubble("The word الرَّحْمَنِ comes from the root ر-ح-م meaning mercy.", false)
        JChatBubble("What's the difference between رَحْمَن and رَحِيم?", true)
        Row(
            Modifier.fillMaxWidth().padding(top = 4.dp),
            horizontalArrangement = Arrangement.spacedBy(6.dp),
        ) {
            listOf("Again" to false, "Hard" to false, "Good" to true, "Easy" to false).forEach { (lbl, active) ->
                val bg = if (active) c.primary else c.bgSurface.copy(alpha = 0.85f)
                Box(
                    Modifier
                        .weight(1f)
                        .height(32.dp)
                        .clip(SquircleShape(12.dp))
                        .background(bg),
                    contentAlignment = Alignment.Center,
                ) {
                    JText(lbl, Jawhar.type.labelS, if (active) c.onPrimary else c.onSurfaceVariant)
                }
            }
        }
        JText(
            "Ask · Learn · Remember",
            Jawhar.type.labelM,
            c.info.copy(alpha = 0.75f),
            Modifier.fillMaxWidth(),
            TextAlign.Center,
        )
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
        JButton("Send reset link", { nav.go(Dest.ResetSent) })
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
