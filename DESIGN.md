# DESIGN.md: Jawhar UI rules for coding agents

Read this file completely before writing or changing any UI in this repo. It is the single source of truth for how Jawhar looks and how UI code is written. If a request conflicts with this file, follow this file and say so. If something here is missing or wrong, ask the user instead of inventing a new style.

The app is named **Jawhar** (never "The Sacred Script"). It is an AI powered Classical Arabic and Quran understanding app (Sarf, Nahw, AI tutor, flashcards, Quran reader). Target users are non-native Arabic speakers, mostly in Pakistan. The learner app is Kotlin Compose Multiplatform (Android, iOS, Desktop, Web). Package: `com.meher.jawhar`.

Related files: `AGENTS.md` (project and backend rules), `docs/specs/` (product specs). This file only covers UI.

---

## 1. Non-negotiable rules

These are the mistakes agents make most. Do not make them.

1. **Use the design system.** Build screens from the `J*` components in `shared/src/design/` and the helpers in `shared/src/screens/Common.kt`. Do not use raw Material3 `Button`, `Card`, `TextField`, `NavigationBar`, `TopAppBar`, `Scaffold`, `AlertDialog`, `ModalBottomSheet`, `Switch` or `FilterChip`.
2. **Never hardcode colours, fonts or sizes of text.** Colours come from `Jawhar.colors.*`, text styles from `Jawhar.type.*`. No `Color(0xFF...)` in screens or components (only `design/Tokens.kt` defines colours). No `fontSize =` overrides except for deliberate scaling such as the reading size setting.
3. **No outlined or hollow cards.** A card is a solid tonal fill with no border. Never draw a stroke around a card, list row, quiz option or tile. Separate surfaces by tone (`bgSurfaceVariant` on `bgBase`), not by borders. Strokes are allowed only for: the 2dp focus ring on text and search fields, the letter circle on a quiz option, and the decorative 8-point star outlines.
4. **No rounded rectangles.** Controls are capsules or circles. Cards and panels use `SquircleShape`. Never use `RoundedCornerShape` for cards or panels (only `CapsuleShape`, which is a 50% rounded shape, and `CircleShape`).
5. **Floating, not docked.** The bottom navigation is the floating capsule `JFloatingNav`. Back, more, close, share and bookmark are floating 48dp circular buttons placed over the content. There is no top app bar and no docked bottom bar anywhere.
6. **Colour means grammar.** The seven role colours (`roleFaail` and the rest) are reserved for Nahw meaning. Never use them as decoration or for status.
7. **Arabic is always right to left and uses the Arabic fonts.** Use `JArabic` for Arabic text, never plain `Text` with a Latin style. Never strip or alter diacritics (tashkeel). Never truncate Arabic with an ellipsis.
8. **Icons come from the `JI` enum** drawn with `JIcon`. No emoji as icons, no Material icon packages, no new image assets for icons.
9. **Every screen must work in light and dark** by using tokens only, and must be registered in the catalog (section 9).
10. **No backend logic in composables.** Screens are UI only and read mock data from `screens/Mock.kt` until the backend exists. See section 11.
11. **No code comments, keep code simple and explainable.** Small composables, no clever abstractions, no new dependencies without asking the user.

---

## 2. Design language in one paragraph

Warm parchment surfaces, malachite green primary, illumination gold accent, serif headlines (Fraunces) with a clean sans for UI (Plus Jakarta Sans), and Naskh Arabic that always gets room to breathe. Calm and serious, like a manuscript, but modern: floating glass capsules for navigation and actions, continuous (squircle) corners, generous spacing, solid tonal cards, and large faint 8-point stars as the only decoration. The ayah is always the hero of a screen.

Principles: reading first; calm warm surfaces; colour means grammar; one thumb and 48dp targets; Material structure with Apple clarity; bilingual by default.

---

## 3. Repo layout and where code goes

```
shared/src/
  App.kt                  entry point, do not add screens here
  LegacyApp.kt            old UI, deprecated, do not extend
  design/                 the design system (tokens, theme, type, shapes, icons, components)
  nav/Nav.kt              JNav (back stack), LocalNav, Dest (screen ids)
  screens/                one file per screen group, plus Common.kt, Mock.kt, Screens.kt, Gallery.kt
  ui/, theme/             LEGACY: old Apple style code. Do not use or copy from it.
shared/composeResources/font/   bundled fonts (do not add other fonts)
```

Old tokens such as `AppleEmerald`, the old `JawharTheme` in `com.meher.jawhar.theme` and `AppleComponents` are legacy. Use only `com.meher.jawhar.design`.

| You are adding | Put it in |
|---|---|
| A new reusable component | `design/` (`Controls.kt`, `Cards.kt` or `Layout.kt`), name it `J<Name>` |
| A helper used by several screens | `screens/Common.kt` |
| A screen | the matching `screens/<Group>Screens.kt`, name it `<Name>Screen` |
| Mock data | `screens/Mock.kt` |
| A new icon | add the entry to the `JI` enum in `design/Icons.kt` as a 24 unit SVG path (see section 8) |

---

## 4. Colour

Always use the tokens. Light and dark values are defined once in `design/Tokens.kt`.

| Kotlin token (`Jawhar.colors.`) | Light | Dark | Use |
|---|---|---|---|
| `bgBase` | #FBF7EE | #0D1513 | Screen background |
| `bgSurface` | #FEFCF7 | #121C19 | Raised surface, glass base, dialogs, sheets |
| `bgSurfaceVariant` | #F5EFE0 | #182420 | Default card, field, list row fill |
| `bgSurfaceHigh` | #EBE3CE | #21302B | Pressed state, switch track, skeletons, progress backing |
| `bgInverse` | #062A25 | #F5EFE0 | Splash, snackbar, admin sidebar |
| `primary` | #0F4A41 | #6FB3A5 | Main actions, active states, links |
| `onPrimary` | #FEFCF7 | #031815 | Content on primary |
| `primaryContainer` | #CFE6E0 | #0A3A33 | Soft green fill, active nav capsule, selected chip |
| `onPrimaryContainer` | #062A25 | #CFE6E0 | Content on primary-container |
| `primarySoft` | #EAF4F1 | #062A25 | Very light green tint (pressed text button) |
| `accent` | #E2A82A | #EFC04F | Rewards, highlight CTA, streak, current lesson |
| `onAccent` | #031815 | #031815 | Content on accent |
| `accentContainer` | #FCEBBE | #523805 | Gold tinted card, warnings |
| `onAccentContainer` | #523805 | #FCEBBE | Content on accent-container |
| `info` | #264A8A | #7A9AD8 | Informational icons and text |
| `infoContainer` | #D2DFF5 | #14274B | Info card, banner |
| `error` | #A3402D | #E59A88 | Errors, destructive actions |
| `errorContainer` | #F8D9D1 | #7F3022 | Error fill |
| `onErrorContainer` | #7F3022 | #F8D9D1 | Content on error-container |
| `success` | #2F7340 | #8CC796 | Success, correct answers |
| `successContainer` | #D3E9D0 | #1E4A29 | Success fill |
| `onSurface` | #1F1C15 | #F5EFE0 | Primary text |
| `onSurfaceVariant` | #6F6650 | #BDB195 | Secondary text |
| `onSurfaceSubtle` | #968B72 | #968B72 | Placeholder, hints, disabled labels |
| `onInverse` | #FBF7EE | #062A25 | Text on inverse surfaces |
| `outline` | #DDD2B8 | #2D3F39 | Inactive dots, rare dividers, thumb off |
| `outlineVariant` | #EBE3CE | #21302B | Hairlines, progress track |
| `scrim` | #050F0D at 50% | #000000 at 60% | Dim behind dialogs and sheets |

Rules:
- Text on `primary` is `onPrimary`, on `primaryContainer` is `onPrimaryContainer`, on `accent` is `onAccent`, and so on. Never put `onSurface` text on a saturated fill.
- Success is `success` on `successContainer`, errors are `error` on `errorContainer`, information is `info` on `infoContainer`, warnings use the accent pair.
- Dim backdrops use `scrim`.
- For tinted fills from a role or status colour use `color.copy(alpha = 0.12f)` (0.14f for tags, 0.28f for a selected word chip).

Grammar role colours (Nahw only):

| Kotlin token | Light | Dark | Grammar role |
|---|---|---|---|
| `roleFaail` | #2F8F5B | #6CCB93 | Fa'il (subject) |
| `roleMaful` | #3A66B0 | #8FB0EA | Maf'ul bihi (object) |
| `roleMubtada` | #C9971A | #F0CB5E | Mubtada (topic) |
| `roleKhabar` | #D9822B | #F2A862 | Khabar (predicate) |
| `roleNat` | #7B5AA6 | #B79BE0 | Na't (adjective) |
| `roleHarf` | #8B8268 | #B8AE93 | Harf (particle) |
| `roleMudaf` | #C0587A | #E89BB4 | Mudaf ilayh (possessor) |

Use them through `GrammarRole` (`GrammarRole.Mubtada.color(Jawhar.colors)`), never directly.

---

## 5. Typography

Fonts are bundled as static files in `composeResources/font/` and loaded in `design/Type.kt`: Fraunces SemiBold (headlines), Plus Jakarta Sans 400/500/600/700 (UI), Newsreader Italic (transliteration), Amiri Quran (ayat), Scheherazade New Regular and Bold (large single words), Amiri Bold (Arabic headings), Noto Sans Arabic 400/500/600 (Arabic UI text).

| Style (`Jawhar.type.`) | Font | Size / line | Use |
|---|---|---|---|
| `displayL` | Fraunces SemiBold | 40 / 48 | Splash wordmark, admin hero |
| `headlineL` | Fraunces SemiBold | 32 / 40 | Screen titles |
| `headlineM` | Fraunces SemiBold | 26 / 32 | Section heroes, welcome titles |
| `headlineS` | Fraunces SemiBold | 22 / 28 | Dialog titles, card numbers |
| `titleL` | Plus Jakarta Sans Bold | 18 / 26 | Section titles |
| `titleM` | Plus Jakarta Sans SemiBold | 16 / 24 | List item titles |
| `titleS` | Plus Jakarta Sans SemiBold | 14 / 20 | Small titles, tags |
| `bodyL` | Plus Jakarta Sans Regular | 16 / 24 | Main body copy |
| `bodyM` | Plus Jakarta Sans Regular | 14 / 22 | Secondary body, chat |
| `bodyS` | Plus Jakarta Sans Regular | 12 / 18 | Captions, helpers |
| `labelL` | Plus Jakarta Sans SemiBold | 14 / 20 | Buttons, chips |
| `labelM` | Plus Jakarta Sans SemiBold | 12 / 16 | Labels, small tags |
| `labelS` | Plus Jakarta Sans Bold | 10 / 14 | Overlines (uppercase) |
| `translit` | Newsreader Italic | 16 / 24 | Transliteration (italic) |
| `arabicQuranXL` | Amiri Quran | 44 / 76 | Focused ayah |
| `arabicQuranL` | Amiri Quran | 32 / 58 | Ayat in the reader |
| `arabicQuranM` | Amiri Quran | 26 / 46 | Ayat in cards, word chips |
| `arabicWordXL` | Scheherazade New Bold | 64 / 96 | Flashcard and lesson hero word |
| `arabicWordL` | Scheherazade New | 40 / 64 | Single words in headers |
| `arabicHeading` | Amiri Bold | 28 / 44 | Arabic headings, surah names |
| `arabicTitle` | Noto Sans Arabic SemiBold | 18 / 30 | Arabic in options, tables |
| `arabicBody` | Noto Sans Arabic Regular | 15 / 26 | Arabic UI body |
| `arabicLabel` | Noto Sans Arabic Medium | 13 / 22 | Arabic UI labels |

Rules:
- Use `JText(text, style, color, ...)` for Latin text and `JArabic(text, style, color, ...)` for Arabic text. `JArabic` forces right to left. Mixed English and Arabic sentences are fine in `JText`. Use `JArabic` whenever a string is Arabic only.
- Overlines (`labelS`) are written uppercase (`JSectionLabel` does this for you).
- Sentence case everywhere ("Start session", not "Start Session"). No exclamation marks in system copy.
- Arabic styles have large line heights on purpose. Do not reduce them, or diacritics will clip.
- Transliteration uses `translit`, always italic and in `onSurfaceVariant`.

---

## 6. Shape, spacing, elevation, glass

**Shapes**

| Element | Shape |
|---|---|
| Buttons, chips, search field, nav, pills, tags, switches, progress bars | `CapsuleShape` |
| Avatars, floating buttons, lesson nodes, badges | `CircleShape` |
| Text field | `SquircleShape(22.dp)` |
| List rows, tiles, quiz options, banners, snackbars | `SquircleShape(24.dp)` to `26.dp` |
| Cards | `SquircleShape(28.dp)` to `34.dp` (30.dp for hero rows, 34.dp for large cards) |
| Dialogs | `SquircleShape(34.dp)` |
| Bottom sheets | `SquircleTop(48.dp)` |
| Illustration and hero panels | `SquircleShape(48.dp)` to `52.dp` |

`SquircleShape` applies the continuous corner (60% smoothing). Use `SquircleShape(topStart, topEnd, bottomEnd, bottomStart)` for uneven corners, as in chat bubbles (the small corner is 6.dp).

**Spacing:** 4dp grid, 8dp rhythm. Screen side padding is 24dp. Default vertical gap in a screen is 16dp. Touch targets are at least 48dp (buttons are 52dp tall, floating buttons 48dp, text fields 56dp, chips 36dp, nav 68dp).

**Elevation:** only floating elements cast a shadow, through `Modifier.softShadow(shape, elevation, alpha)` (tinted deep green, never black). Cards are flat. Do not use `Modifier.shadow` or Material elevation directly.

**Glass:** floating elements (`JFloatingButton`, `JGlassPill`, `JFloatingNav`, the tutor composer, the reader toolbar) use `bgSurface` at 92 to 95% opacity plus `softShadow`. This is the "translucent" style. See section 12 for the planned blur and liquid glass options. Never fake glass with gradients or borders.

**Decoration:** the only decoration is the faint 8-point star outline, via `Modifier.starOrnaments(color, StarSpec(...))`, placed inside clipped hero panels at 10 to 40% opacity. Do not add other ornaments, illustrations or gradients.

---

## 7. Screen anatomy

Every screen is built with `Page(...)` (which wraps `JScreen`). Do not build a screen from a bare `Column` or `Scaffold`.

```kotlin
@Composable
fun ExampleScreen() {
    val nav = LocalNav.current
    Page(
        title = "Example",
        right = JI.More,
        cta = { JButton("Continue", { nav.go(Dest.Home) }) },
    ) {
        BigTitle("Heading", "Subtitle")
        JListItem("Row", subtitle = "Supporting text", icon = JI.Star)
    }
}
```

`Page` parameters: `title` (centred glass pill), `right` and `onRight` (floating action button), `back` (default true, shows the floating back button), `backIcon` (`JI.Close` for flows that can be abandoned), `tab` (shows the floating nav with that tab selected and hides the back button), `cta` (bottom action slot with a fade), `scroll`, `spacing`, `overlay` (for dialogs and sheets), `background`.

Layout facts (do not change):
- Content scrolls under the floating elements. The top inset plus 68dp is reserved above the content; floating buttons sit 8dp below the status bar and 16dp from the sides.
- Bottom space of 120dp is reserved when a nav or `cta` is present. A gradient fade (`bgBase` transparent to opaque) sits behind them.
- `cta` sits 22dp from the bottom with 24dp side padding. Primary action first, text-style secondary action below it.
- Progress at the top of a flow (lesson, placement test) uses `overlay = { TopProgress(progress, "3 / 5") }` next to a `JI.Close` back button.
- Tab root screens (`Home`, `Learn`, `Quran`, `Tutor`, `Profile`) use `Page(back = false, tab = JTab.X)`.
- Large title for tab roots: a `JText(..., headlineL)` at the top of the content, not an app bar.
- Hero cards: `HeroCard` (solid fill, optional star ornaments, 34dp squircle).
- Dialogs and sheets are overlays rendered inside the screen with `JDialog` and `JBottomSheet` (never platform dialogs).

---

## 8. Icons

`JI` is an enum of 60 stroke icons on a 24 unit grid (1.8dp round stroke), drawn by `JIcon(icon, size, tint, strokeWidth, filled)`. Default size is 24.dp; use 20.dp inside tiles and rows, 22.dp in buttons and nav. Filled style is used only for the play icon on the current lesson node. To add an icon, add a `JI` entry with an SVG path on a 24 by 24 grid (stroke only, round caps). Always tint with a token.

Existing icons: Home, Learn, Quran, Tutor, User, Flame, Search, Back, Chevron, ChevronDown, Close, Check, Bell, Sliders, Send, Eye, EyeOff, Lock, Mail, Trophy, Bookmark, Cards, Play, Refresh, WifiOff, Alert, Info, Trash, Edit, Logout, Tree, Moon, Globe, Target, Star, Shield, Plus, More, Share, Grid, Mic, Clock, Users, Bolt, Flag, Calendar, Bulb, Doc, Help, Chart, Sun, Heart, Download, Pause, Spark, Layers, Signal, Wifi, Battery, Volume.

---

## 9. Component catalog

Use these before creating anything new. Parameters in brackets are optional.

**Text and decoration**

| Component | Purpose |
|---|---|
| `JText(text, style, [color, modifier, textAlign, maxLines, overflow])` | All Latin text |
| `JArabic(text, [style, color, modifier, textAlign])` | All Arabic text, forces right to left |
| `JIcon(icon, [modifier, size, tint, strokeWidth, filled])` | Icons |
| `JLogoMark([modifier, size, background])` | App logo (squircle, gold star, letter ج) |
| `JStarBadge(label, [modifier, size, fill, textColor])` | Numbered 8-point star (surah and ayah numbers) |
| `Modifier.starOrnaments(color, vararg StarSpec)` | Faint decorative star outlines |
| `JTag(text, [modifier, background, color, icon, height])` | Small capsule label |
| `JSectionLabel(text)` | Uppercase overline above a group |

**Controls**

| Component | Purpose |
|---|---|
| `JButton(text, onClick, [modifier, style, enabled, icon, height])` | Styles: Filled, Tonal, Neutral, Text, Accent. 52dp tall capsule. One Filled button per screen |
| `JFloatingButton(icon, onClick, [modifier, filled, size])` | 48dp floating circle (glass) |
| `JGlassPill(text)` | Floating title pill |
| `JTextField(value, onValueChange, label, [placeholder, helper, isError, password, trailing, keyboardType])` | Filled field, label above, helper below. Use `StatefulField` for UI-only screens |
| `JSearchField(value, onValueChange, placeholder)` | Capsule search field |
| `JChip(label, selected, onClick)` | Filter chip (selected shows a check) |
| `JSwitch(checked, onCheckedChange)` | Switch |
| `JSegmented(options, selected, onSelect)` | Segmented control |
| `JSlider(value, onValueChange)` | Slider |
| `JFloatingNav(selected, onSelect)` | The five-tab floating bar: Home, Learn, Quran, Tutor, Profile |

**Surfaces and feedback**

| Component | Purpose |
|---|---|
| `JCard([modifier, color, radius, padding]) { }` | Solid tonal card |
| `JListItem(title, [subtitle, icon, tile, tileTint, onClick, trailing])` | Row with icon tile. Pass `trailing = null` for none, or a lambda for a switch or value |
| `JInfoCard(title, body, [tone, icon])` | Tone: Neutral, Primary, Accent, Info |
| `JBanner(kind, title, message, [floating])` | Kinds: Info, Success, Warning, Error, Offline |
| `JSnackbar(message, action, [kind, onAction])` | Inverse toast |
| `JDialog(title, body, confirm, onConfirm, onDismiss, [cancel, icon, destructive])` | Centered dialog with scrim |
| `JBottomSheet(onDismiss) { }` | Bottom sheet with handle and scrim |
| `JScrim(onClick)` | Dim backdrop |
| `JSkeleton([modifier, radius, color])` | Loading placeholder shape |
| `JCenterState(icon, tile, tint, title, body)` | Icon circle, title and body for empty and error content |

**Learning**

| Component | Purpose |
|---|---|
| `JQuizOption(text, letter, state, onClick, [arabic])` | States: Default, Selected, Correct, Incorrect |
| `JWordChip(word, role, [selected, onClick])` | Grammar role chip (Nahw) |
| `JLessonNode(label, state, [onClick])` | Learning path node: Completed, Current, Locked |
| `JRatingButton(rating, onClick)` | SM-2 rating: Again, Hard, Good, Easy |
| `JStatTile(icon, value, label, fill, tint)` | Stat tile (streak, XP, words) |
| `JBadgeTile(title, caption, unlocked)` | Achievement badge |
| `JProgressBar(progress, [modifier, height, track, fill])` and `JProgressRing(progress, ...)` | Progress |
| `JChatBubble(text, fromUser)` | Tutor and user bubbles |
| `JAvatar(initials, [size])` | Initials avatar |

**Screen helpers (`screens/Common.kt`)**

`Page`, `BigTitle(text, [sub, center])`, `SectionTitle(text, [action])`, `HeroCard`, `StatefulField`, `CircleIcon`, `TwoButtons`, `OrDivider`, `FooterLink`, `PageDots`, `TopProgress`, `CheckRow`, `StateScreen` (full-screen empty, error and offline pattern), `AyahWords` and `AyahBlock` in `QuranScreens.kt` (ayah text with tappable, highlightable words).

If you need a component that does not exist, first check this list, then add a new `J` component in `design/` following the same patterns (tokens only, squircle or capsule, no stroke), then add it to this file.

---

## 10. Navigation and the screen catalog

- Navigation is `JNav` (a simple back stack) provided as `LocalNav`. Use `nav.go(Dest.X)`, `nav.back()`, `nav.reset(Dest.X)` and `nav.tab(JTab.X)`. Do not add a navigation library without asking.
- Screen ids are constants in `Dest` (`nav/Nav.kt`).
- **Every screen must be registered** in `Screens.all` in `screens/Screens.kt` with an id, a group name and a title. The catalog panel (desktop and web) is generated from it. State and edge case screens use ids such as `s_login_error` and dark mode variants wrap the screen in `JawharTheme(dark = true)`.

To add a screen: write `<Name>Screen()` in the right group file using `Page`, add a `Dest` constant if it is navigated to, and add a `ScreenSpec` to `Screens.all`.

Current set: 85 screens in groups: onboarding and auth (01 to 14), home and learn (15 to 21), Quran, Sarf and Nahw (22 to 30), tutor and flashcards (31 to 37), progress and profile (38 to 46), states and edge cases (S01 to S28), dark mode (D01 to D07) and the admin dashboard for web (A01 to A04, wide layout).

---

## 11. State, data and backend

- Screens are UI. Keep state local (`remember`) only for UI concerns such as the selected chip or a text field. Hoist everything else so a view model can drive it later.
- Mock data lives in `screens/Mock.kt`. When the backend exists, replace `Mock` reads with view model state and replace empty click handlers with calls. Keep composable signatures simple (plain values and lambdas, no repository or network types).
- Every screen that loads data needs all of: a loading state (`JSkeleton`), an empty state (`JCenterState`), an error state and an offline state. The patterns already exist as the S-screens (`StateScreen`, `SkeletonHomeScreen`, `OfflineBannerScreen`, `SarfEngineScreen(timeout = true)`, `TutorChatScreen(error = true)`). Reuse them.
- Destructive actions (delete account, leave lesson, log out) always confirm with `JDialog`. Delete is `destructive = true`.
- Internet is required. There is no offline mode in scope.

---

## 12. Glass options (blur and liquid glass)

Current behaviour: translucent surfaces plus shadow (section 6). Planned: a user-facing setting with three choices, **Translucent** (default, current), **Blur** (real background blur using the Haze library) and **Liquid glass** (experimental, blur plus tint and a bright edge, lens effects only if the library supports them).

Rules for agents implementing or touching this:
- All glass surfaces must go through one shared modifier in `design/` (for example `Modifier.glass(shape)`), never per-component blur code. Today the glass look is inlined in `JFloatingButton`, `JGlassPill`, `JFloatingNav`, the tutor `Composer` and the reader toolbar; when the modifier exists, move them onto it.
- Glass is only for floating elements that sit over scrolling content. Cards, list rows and dialog bodies stay solid.
- Provide a fallback (the translucent style) when blur is unavailable or the setting is off. Blur has a performance cost, so keep it to the few floating elements.
- Do not add the Haze dependency or an effect without the user confirming the library version.

---

## 13. Content and copy

- Brand voice: calm, clear, encouraging, never childish. No emoji in UI copy.
- Sentence case, short labels ("Start session", "Show answer", "Build my learning path"). Errors say what happened and what to do next.
- Never invent Quran text or grammar. Use correct, fully vowelled Arabic. Sample data uses Surah Al-Fatiha and the root ك ت ب. Translations in mock data are placeholder paraphrases, not a quoted translation; real translation sources must be confirmed by the user.
- Sample numbers (XP, streaks, scores) are placeholders.
- There are no ads and no monetisation in this app. Do not add them.
- Out of scope (do not design): Tajweed or audio correction, hifz features, Modern Standard Arabic or dialects, a desktop or web learner app, offline mode, subscriptions.

---

## 14. Code conventions

- Kotlin, Compose Multiplatform, built with the Kotlin Toolchain (`./kotlin build`, `./kotlin run -m desktopApp`). Common code only in `shared/src`; no platform-specific APIs in the design system.
- Components are named `J<Name>`, screens `<Name>Screen`, tokens accessed through `Jawhar.colors` and `Jawhar.type`.
- No comments in code. Keep functions small and readable. Prefer composition over configuration flags.
- Stable APIs only. Experimental APIs need an `@OptIn` and a reason in your message (for example `FlowRow` already uses `ExperimentalLayoutApi`).
- Do not add dependencies, fonts, image assets or new colours without asking.
- After changes run `./kotlin build` and fix every error and new warning before finishing.

---

## 15. Common wrong outputs to avoid

| Wrong | Right |
|---|---|
| `Card(border = BorderStroke(...))`, outlined or bordered cards | `JCard` or a `Modifier.clip(SquircleShape(..)).background(token)` |
| `RoundedCornerShape(12.dp)` on a card | `SquircleShape(28.dp)` |
| `NavigationBar`, `BottomAppBar`, `TopAppBar`, `CenterAlignedTopAppBar` | `Page(tab = ...)`, `JFloatingNav`, `JFloatingButton` |
| `Color(0xFF0F766E)`, the old emerald, system blue, Material purple | `Jawhar.colors.primary` and the other tokens |
| `Text("..", fontSize = 18.sp)` | `JText("..", Jawhar.type.titleL)` |
| Arabic in `Text` with a Latin font, `textAlign = Center` hacks | `JArabic(..)` |
| Emoji tab icons, Material icon packages | `JIcon(JI.X)` |
| Platform `AlertDialog` or `ModalBottomSheet` | `JDialog`, `JBottomSheet` in the `overlay` slot |
| A new button style in a screen | One of the five `JButtonStyle` values |
| Role colours used for status or decoration | Status pairs (`success`, `error`, `info`, accent) |
| Hard drop shadows, gradients, glow | `softShadow` on floating elements only |
| Screens that only work in light mode | Tokens only, check the dark variant in the catalog |
| Writing business logic or network calls inside a screen | Keep screens UI only, read mock or hoisted state |

---

## 16. Pre-merge checklist

1. Built only from `design/` components and `Common.kt` helpers; no new hex colours or text sizes.
2. No outlined cards, no rounded rectangles, no docked bars, no emoji.
3. Arabic uses `JArabic`; diacritics intact; nothing truncated.
4. Works in dark mode (open the dark variant or `JawharTheme(dark = true)`).
5. Loading, empty, error and offline states exist where data is loaded.
6. Registered in `Screens.all` and `Dest` if navigable.
7. `./kotlin build` passes with no new errors or warnings.
8. This file updated if a component, token or rule changed.

---

## 17. Design source files

The visual reference for every screen lives outside the repo: the Figma file, the SVG and PNG screen package (`Jawhar_Screens`) and `Jawhar_Design_Handoff.md`. The numbers in screen titles (01 to 46, S01 to S28, D01 to D07, A01 to A04) match those files. When the code and the design disagree, ask the user which one is right before changing either.