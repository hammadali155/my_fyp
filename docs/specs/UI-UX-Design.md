# UI/UX Design Document

## AI-Powered Classical Arabic & Quranic Learning Platform

**Version:** 1.0  
**Date:** 2026-03-25  
**Author:** Meher Ali (FA23-BCS-059)  
**Status:** Draft

---

## 1. Design Principles

### 1.1 Core Principles
1. **Quran-first, learner-second:** The Quranic text is the hero. Arabic script is always legible, beautifully rendered, and never visually degraded.
2. **Grammar made visual:** Abstract Nahw/Sarf concepts must be observable — color, layout, and motion reveal linguistic structure that text alone hides.
3. **Beginner-safe:** No researcher UI. Every screen answers "what do I do now and why."
4. **Bidirectional Cues:** RTL Arabic layout with LTR UI chrome; clear visual transitions at language boundaries.
5. **Calm & Focused:** Islamic aesthetic — deep greens, gold accents, generous whitespace. No distracting gamification noise before learning value.

### 1.2 Emotional Design
- **Aura:** reverence + clarity (scholarly but approachable)
- **Tone:** warm, encouraging, precise
- **Avoid:** gimmicks, loud confetti, cartoonish mascots

---

## 2. Design System

### 2.1 Color Palette

| Token | Hex | Usage |
|-------|-----|-------|
| `--emerald-forest` | `#0B6B4F` | Primary action, focus states |
| `--emerald-deep` | `#084C36` | Primary dark / headers |
| `--gold` | `#C9A227` | Accents, achievements |
| `--sand-bg` | `#F7F4EE` | App background (warm paper) |
| `--ink` | `#1F2937` | Primary text |
| `--ink-soft` | `#6B7280` | Secondary text |
| `--white` | `#FFFFFF` | Cards, surfaces |
| `--error` | `#B3261E` | Errors, wrong answers |
| `--success` | `#1B7A3D` | Correct answers |

### 2.2 Arabic Verse / Word Highlight Colors (Nahw)

| Nahw Role | Color | Hex |
|-----------|-------|-----|
| فاعل (Subject) | Blue | `#2563EB` |
| مفعول به (Object) | Orange | `#D97706` |
| مبتدأ (Mubtada) | Purple | `#7C3AED` |
| خبر (Khabar) | Green | `#059669` |
| نعت (Adjective) | Teal | `#0D9488` |
| حرف جر (Preposition) | Pink | `#DB2777` |
| ظرف (Adverb) | Brown | `#92400E` |
| حال (Circumstantial) | Indigo | `#4F46E5` |
| Other / Unmarked | Gray | `#9CA3AF` |

**Legend rule:** every Nahw view must show a color legend. Never rely on color alone — each colored word carries a small role label tag for accessibility.

### 2.3 Typography

| Role | Font | Fallback |
|------|------|----------|
| Arabic (Quranic) | Amiri Quran / `Amiri` | Noto Naskh Arabic |
| Arabic (UI) | Noto Naskh Arabic | Amiri |
| Latin (UI, headings) | Inter | system sans |
| Latin (UI, body) | Inter | system sans |
| Monospace (code/API) | JetBrains Mono | ui-monospace |

Rules:
- Arabic base size ≥ 22px on mobile for reading comfort
- Uthmanic-style numerals (٠١٢٣) inside Quranic text; Western numerals in UI labels
- Line-height for Arabic: ≥ 1.8 (diacritics need vertical room)

### 2.4 Spacing & Radius

| Token | Value | Usage |
|-------|-------|-------|
| `space-1` | 4px | Tight inline gaps |
| `space-2` | 8px | Input padding, small cards |
| `space-3` | 12px | Standard gaps |
| `space-4` | 16px | Card padding |
| `space-6` | 24px | Section gaps |
| `space-8` | 32px | Screen padding |
| `radius-sm` | 8px | Inputs, chips |
| `radius-md` | 12px | Cards |
| `radius-lg` | 16px | Modals, sheets |
| `radius-full` | 999px | Badges, avatars |

### 2.5 Elevation
- Cards: `0 1px 2px rgba(31,41,55,0.06)` + `0 1px 3px rgba(31,41,55,0.10)`
- Floating action / modal: `0 8px 24px rgba(31,41,55,0.18)`

### 2.6 Iconography
- Line icons (Lucide-style), 24px default
- Arabic amulets/motifs reserved for branding only
- Icons must not be the only label (text + icon in nav)

### 2.7 Motion
- Transitions: 150–250ms ease-out
- Arabic text reveal: fade + slight rise (never jittery/horizontal — Arabic legibility)
- Complete-lesson celebration: subtle gold pulse, no confetti storm

---

## 3. Screen Inventory

### 3.1 All Platforms (Compose Multiplatform — Android / iOS / Desktop / Web)

One shared Compose UI codebase; the screen inventory below is platform-agnostic. Route/destination names are logical (used by Compose Navigation on JVM/Android/iOS and the Web target):

| Route | Screen | Purpose |
|-------|--------|---------|
| `/` | Landing | Pitch, features, CTA |
| `/login` `/register` | Auth | Sign in / up |
| `/app` | Dashboard | Today's plan, streak, continue lesson |
| `/app/learn` | Learning Path | Lesson map, locked/unlocked |
| `/app/lesson/:id` | Lesson Player | Content, examples, exercises |
| `/app/sarf` | Sarf Analyzer | Word input → morphology result |
| `/app/nahw` | Nahw Parser | Verse/sentence input → annotated |
| `/app/nahw/verse/:sura::ayah` | Verse Annotation | Pre-made annotation view |
| `/app/words` | Vocabulary | Decks, review queue, stats |
| `/app/review` | SRS Session | Card review screen |
| `/app/tutor` | AI Tutor Chat | Conversational assistant |
| `/app/progress` | Progress | Charts, badges, mastery |
| `/app/settings` | Settings | Profile, preferences, RTL toggle |

### 3.2 Mobile Navigation (Android / iOS)

Bottom Tab Bar (5 tabs), shared across Android/iOS:
1. **Home** (Dashboard) — book/open-quran icon
2. **Learn** (Learning Path + Lesson Player)
3. **Analyze** (Hub: Sarf / Nahw quick access) — center emphasized action
4. **Review** (SRS queue)
5. **Tutor** (Chat)

All screen destinations above are shared; phone targets use the bottom tab bar + stacked navigation, wide targets use the sidebar.

---

## 4. Key Screen Specifications

### 4.1 Onboarding — First Run (Mobile priority)

**Step flow:**
1. Welcome (brand + value prop, language selector AR/EN)
2. Goal selection (cards: Understand the Quran / Study grammar / Memorize vocab)
3. Level screening (3-question quick check) → routes to onboarding assessment
4. Assessment start CTA (20 questions, ~10 min, progress bar)

**Layout spec:** centered card on gold-gradient background; one question per screen; progress dots; Arabic toggle for question text.

### 4.2 Dashboard (Home)

```
┌───────────────────────────────┐
│ ☰  الاسم  [Bismillah]   ⚙    │  header
│  Assalamu alaikum, Meher      │
│  Level: Intermediate          │  level chip
├───────────────────────────────┤
│ ┌───────────────────────────┐ │
│ │  Streak 🔥 12   Due today │ │  stats row
│ │  ·  32 cards · 15 min     │ │
│ │  [Start Review →]         │ │
│ └───────────────────────────┘ │
│ ┌───────────────────────────┐ │
│ │ Next in your path          │ │
│ │ Sarf Lesson 7: باب تفعيل   │ │
│ │ ▓▓▓▓▓▓░░ 62% progression  │ │
│ │ [Continue →]               │ │
│ └───────────────────────────┘ │
│  Quick actions:               │
│  [Sarf] [Nahw] [Tutor]        │  segmented grid
│  Recent verses studied:       │
│   ٱلْحَمْدُ لِلَّهِ رَبِّ ... │  verse preview
└───────────────────────────────┘
```

**Empty states:** first-run — full onboarding CTA; no reviews due — "All caught up! ✦ new words to learn?"

### 4.3 SRS Review Screen

```
┌───────────────────────────────┐
│  Review · 32/50     10:14    │  counter + timer
├───────────────────────────────┤
│                               │
│      وَالْكِتَابِ            │  big Arabic word
│                               │
│  [Show meaning & analysis]    │  reveal button
│                               │
├───────────────────────────────┤
│  revealed panel:              │
│  root: ك ت ب | pattern: فعال  │
│  "and the Book" · example:    │
│  يَا أَيُّهَا الرَّسُولُ ...  │
├───────────────────────────────┤
│  How well did you know it?    │
│  [Again][Hard][Good][Easy]    │  4 button rating
└───────────────────────────────┘
```

- RTL: Arabic on top; LTR gloss below
- Rating buttons: horizontal, color-coded (red/amber/green/teal)
- Optional keyboard shortcuts: 1–4 (desktop)

### 4.4 Sarf Analyzer

```
┌────────────────────────────────┐
│  Sarf Engine   [⚙ model:CAMeL] │
│  [ input word: كَتَبَ     ] ▶ │
├────────────────────────────────┤
│  Result for: كَتَبَ            │
│  Root: ك ت ب   Pattern: فَعَلَ │
│  Form: I | Past | Active | 3sg │
│  ┌────────────────┐            │
│  │ conjugation    │            │
│  │ table (grid)   │            │
│  └────────────────┘            │
│  Quranic occurrences (12):     │
│  ✦ 2:255  ... فِيهِمَا كَتُبَ │
│  ✦ 2:282  يَٰٓأَيُّهَا ...    │
│  [See in Nahw →] [Add to deck] │
└────────────────────────────────┘
```

### 4.5 Nahw Parser (Verse Annotation, the signature screen)

```
┌────────────────────────────────────────┐
│  36:12  إِنَّا نَحْنُ نُحْيِ الْمَوْتَىٰ│
│  Legend:  [Subject][Object][Mubtada]...│
├────────────────────────────────────────┤
│  إِنَّا   نَحْنُ   نُحْيِ   الْمَوْتَىٰ  │
│ ┌─────┐ ┌────┐ ┌────┐ ┌────────┐      │
│ │حرف │ │مبتدأ│ │فعل│ │مفعول به│      │
│ │ناسخ│ │  خبر │ │مضارع│ │        │      │
│ └─────┘ └────┘ └────┘ └────────┘      │
│  tap any word → detail sheet:           │
│  • POS, i'rab case, root               │
│  • nahw role + translation             │
│  • dependency arrows overlay toggle    │
├────────────────────────────────────────┤
│  [Ask Tutor about this verse →]        │
│  [Add words to SRS (3 selected)]       │
└────────────────────────────────────────┘
```

Key interactions:
- Tap word → bottom sheet detail (mobile) / side panel (web)
- Dependency overlay: animated arrows between heads/dependents (toggle)
- Mode switch: `Nahw (grammar)` | `Sarf (word structure)` | `Literal translation`

### 4.6 AI Tutor Chat

```
┌──────────────────────────────┐
│  AI Tutor  ● ● ● [clear]    │
│  Wed, you reached Lesson 5.  │  context chip
│  Ask anything about Sarf or  │
│  Nahw with Quranic examples. │
├──────────────────────────────┤
│  U: What is مفعول به?         │
│  T: In Classical Arabic,     │
│  المفعول به is the object... │
│  Quran: surat Al-Fatiha 1:5  │
│  إِيَّاكَ نَعْبُدُ ...        │
│  *inline verse renders as    │
│  tappable chip*              │
├──────────────────────────────┤
│  [quick chips: Quiz me |      │
│   Explain this word | ...]   │
│  [ input.....................]│
└──────────────────────────────┘
```

Features:
- Streaming response (SSE), RTL-aware message bubbles (user right, tutor left)
- Tappable Quranic citations → opens verse annotation
- Message actions: copy, re-ask, include in lesson

### 4.7 Learning Path Map

```
Curriculum map (vertical timeline, scrollable):
  Level: Beginner
   ○ Lesson 1: Nouns & gender      ✓ done
   ○ Lesson 2: Definite article    ✓ done
   ● Lesson 3: Verbal sentence     ◉ current
   ○ Lesson 4: فاعل (subject)      🔒 locked
   ○ Lesson 5: ...                 🔒 locked
   [Progress bar per level]
```

Node states: `done` (check), `current` (pulsing gold ring), `available`, `locked` (padlock + tooltip "Complete Lesson 3 to unlock").

---

## 5. Responsive & RTL Behavior

### 5.1 Breakpoints (Window-size classes)
| Window | Width | Notes |
|--------|-------|-------|
| Compact (phone) | < 640px | Single column, bottom tab bar |
| Medium (tablet / small desktop) | 640–1024px | 1–2 columns, side nav collapses |
| Expanded (desktop / web) | > 1024px | Two-panel layouts, full sidebar |

Same shared Compose UI reacts via `WindowSizeClass`; no per-platform forks.

### 5.2 RTL
- Wrap the app root in `CompositionLocalProvider(LocalLayoutDirection provides LayoutDirection.Rtl)` for Arabic builds; Compose layouts and `contentAlignment` are layout-direction aware automatically
- Arabic first in mixed lines: `قَالَ اللهُ (Allah said)`
- Mirror all directional icons (arrows, chevrons, spinners)

### 5.3 Font / Diacritic Clipping Protection
- Arabic text: `lineHeight` ≥ 1.8 × `fontSize`; never clip glyph bounds (`overflow` disabled on Arabic `Text` composables and containers)
- Never wrap Arabic in `maxLines = 1` without an overflow fallback (ellipsis shapes break diacritics)
- Golden test: render 2:255 with full diacritics — assert no glyph clipping

---

## 6. Accessibility

- WCAG 2.1 AA: contrast (all text ≥ 4.5:1), focus states visible
- Compose `Modifier.semantics` / `contentDescription` on icon-only buttons; `liveRegion` for live SRS progress
- Screen-reader pattern for Arabic Q&A: announce word + meaning, never "colored blue"
- Touch targets ≥ 44px, rating buttons ≥ 56px tall
- Reduced-motion: respect the platform reduced-motion setting (accessibility manager / `System` API), replace animations with static states
- Font scaling: Arabic min 22sp, honors system font scaling (Compose local density) without layout break

---

## 7. Microcopy & Tone

| Context | Copy Example |
|---------|--------------|
| Correct answer | Progress with excellence. ✓ |
| Wrong answer | Not quite. Here's the rule: ... |
| Lesson complete | MashaAllah — Lesson 7 complete. |
| Streak lost | Yesterday was rest day for your memory. Begin anew. |
| Didn't know word | No problem. Reviewing it again tomorrow. |
| AI Tutor limit | You've asked a lot today. Reflect, then resume tomorrow. |

No exclamation overload. No guilt-trip streak messaging. Encouragement grounded in Islamic etiquette (أدب).

---

## 8. Design Review Checklist

Before build, each screen must satisfy:
1. Quranic text legible at 22px+ with full diacritics
2. Color legend present wherever Nahw roles appear
3. RTL/LTR content tested in both script directions
4. Empty, loading, and error states designed (no blank screens)
5. Touch targets ≥ 44px mobile
6. Contrast passes AA
7. A literal English/Urdu gloss available for each Arabic surface
8. Keyboard shortcut exists for rating (desktop)

---

## 9. Open UI Questions
1. Landing page: static single-page vs multi-section marketing page? (design both states)
2. Need a print/export view for annotated verses (for teachers)? — propose later if requested
3. Dark mode in v1 scope? Proposal doesn't mention it; recommend deferring to v1.1 unless requested.