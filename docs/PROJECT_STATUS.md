# Jawhar (جوهر) — Comprehensive Project Status & Roadmap

**Date:** 2026-10-16  
**Project:** AI-Powered Classical Arabic & Quranic Learning Platform (Final Year Project)  
**Monorepo:** `backend/` (FastAPI), `shared/` (Compose Multiplatform), `desktopApp/`, `androidApp/`, `iosApp/`, `webApp/`

---

## 1. Executive Summary

Jawhar is an end-to-end Classical Arabic and Quranic learning system combining linguistic morphology (*Sarf*), syntax (*Nahw*), spaced repetition vocabulary (*SRS*), and AI-guided tutoring.

The foundation, corpus ingestion, morphology engine, SRS core, and the entire multiplatform frontend UI (88 catalogued visual states, custom design system, real API wiring, and Material 3 Expressive motion) are **complete and functional**. 

The primary remaining modules are **Nahw (Syntax Parsing & Tree)**, **Gemini AI Tutor**, **Adaptive Curriculum/Lesson Engine**, and **Redis/Production infrastructure**.

---

## 2. Completed Work So Far

### A. Data Ingestion & Database (100% Complete)
- **Complete Quranic Corpus Ingested**:
  - **114 Surahs**, **6,236 Ayahs**, **77,429 Words**, and **77,429 syntactic annotations** ingested verbatim from the Quranic Arabic Corpus (EQTB) with 0 word-count discrepancies.
- **Rich Word Attributes**:
  - `words` table extended with `pattern`, `tense`, `voice`, `gender`, `number`, `person`, `features_json`, and English translation glosses (`translation_en`).
- **Relational Models & Migrations**:
  - `users`, `verses`, `words`, `surahs`, `srs_cards`, `srs_review_logs`, `decks`, `deck_words`, `badges`, `user_badges`, and `bookmarks` managed via Alembic migrations.

### B. Backend Services & REST APIs (`backend/app/api/v1/`)
- **Authentication & Security**:
  - JWT access/refresh token rotation, password hashing with bcrypt, `/auth/register`, `/auth/login`, `/auth/refresh`, `/auth/me`, profile update.
- **Quran Core Endpoints**:
  - `GET /quran/surahs`: list all 114 chapters.
  - `GET /quran/verses`: paginated verses filtered by `surah_id`, `juz_number`, `page_number`.
  - `GET /quran/surahs/{n}/verses/{m}`: single verse lookup with words and grammatical annotations.
  - `GET /quran/search`: diacritic-insensitive Arabic search with matched field tracking.
  - `GET /quran/roots`: corpus roots ranked by frequency with POS and surah filters.
- **Morphology / Sarf Service**:
  - Clitic segmentation, root lookup, verb Forms I–X catalog detection.
  - Optional CAMeL Tools NLP integration with LRU memoization and fallback pipeline (`corpus` $\to$ `camel` $\to$ `rules`).
  - `POST /morphology/conjugate`: Sound root conjugation across 13 grammatical persons for past, present, and imperative.
  - `GET /morphology/word-family/{root}`: Lemma clusters grouped by part-of-speech with real Quranic verse occurrences.
  - `GET /morphology/patterns`: Complete catalog of verb forms and noun patterns.
- **Spaced Repetition (SRS) Engine**:
  - SM-2 variant implementation with learning, review, and graduated states (ratings 1–4).
  - Endpoints: `GET /srs/due`, `POST /srs/review`, `GET /srs/stats`, `POST /srs/cards`.
  - Seeded default top-100 Quranic roots deck (`scripts/seed_default_deck.py`).
- **Gamification & User Progress**:
  - Atomic review streak updates (`streak_days`, `last_review_date` UTC) and XP increments.
  - Badges system with unlock tracking (`GET /progress/badges`).
- **Bookmarks & Decks Management**:
  - User-scoped verse bookmarks with personal study notes and collections.
  - Custom decks with single and bulk word addition endpoints.
- **System Health**:
  - `GET /health` (DB connectivity, uptime, version), `/health/ready`, `/health/live`.

---

### C. Multiplatform Frontend (`shared/` Compose Multiplatform)
- **Custom Design System (`shared/src/design/`)**:
  - Full theme system (`JawharTheme`, light/dark color tokens, elevation, soft shadows, Islamic 8-point star canvas ornaments).
  - 7 standardized Arabic grammar (*I'rab*) color tokens (Fa'il, Maf'ul, Mudaf, etc.).
  - Typography scales for both Arabic script (`amiri`, RTL layout wrapper `JArabic`) and Latin scripts.
  - Component library: `JButton`, `JInput`, `JCard`, `JArabicCard`, `JFloatingNav`, `PageDots`, `SquircleShape`, `JChatBubble`.
- **Screen Registry (88 catalogued states, 51 routable)**:
  - `Screens.kt` holds one `ScreenSpec` per *visual state* with a `real` flag. `Screens.real` (51) is what the app can navigate to; `Screens.byId` (all 88) is the design-review gallery, shown only when `AppState.galleryEnabled` is true. Keeping state variants out of the router is what stops an error banner from becoming a destination.
- **KMP Ktor API Client (`shared/src/data/api/`)**:
  - Multiplatform HTTP client (`android`, `jvm`, `ios`, `wasmJs`).
  - Serialized DTOs matching backend schema with bearer token injection and session management.
- **Real Backend API Wiring**:
  - `HomeScreen` (live user stats, streak, daily queue, continue reading).
  - `SurahListScreen` (real surahs from API with search/filtering).
  - `SearchScreen` (corpus-wide keyword search).
  - `SarfEngineScreen` (root analysis, occurrences, pattern breakdown).
  - `WordFamilyScreen` & `ConjugationScreen` (live lemma clusters & conjugation tables).
  - `FlashcardScreen` & `VocabularyScreen` (live SM-2 review queue and ratings).
  - `ProfileScreen` & `BadgesScreen` (user stats, XP, unlocked badges).
  - `LogInScreen` & `SignUpScreen` (auth session handling).
- **Progressive Navigation Flow**:
  - Natural progressive app lifecycle: Splash $\to$ Onboarding $\to$ Auth / Placement $\to$ Main Tab Shell (`Home`, `Learn`, `Quran`, `Tutor`, `Profile`) $\to$ Surah Reader.
  - Gallery drawer hidden behind `AppState.galleryEnabled = false`.
- **Material 3 Expressive Motion**:
  - Every animation reads from `design/Motion.kt`. Spatial springs (movement, may overshoot) and effects springs (colour/opacity, damping 1, land dead on target), values taken from the `expressive` scheme at m3.material.io, generic in `T` so one spring drives `Float`, `Dp` and `Color`.
  - Press feedback is the Expressive signature: `JButton` morphs its corner radius from a full capsule to a 14dp rounded rectangle with a container-colour shift. **Nothing shrinks on press** — `tappable` (cards, list rows, chips) uses a state layer at 0.9 alpha instead.
  - Screen push/pop and tab crossfade run on springs. `JBottomSheet` fades its scrim and springs the panel up, and takes a `visible` flag so it stays composed long enough to animate out.
  - `JawharMotion.reduced` collapses every spec to a snap; not yet wired to the platform "remove animations" setting, because Compose Multiplatform does not expose it to shared code.
  - Onboarding guide: swipeable `HorizontalPager`, fixed 360dp card height, morphing vector scenes (Quran emblem, Sarf word family, Tutor dialog), and dynamic button transformations (Next $\to$ Back/Next $\to$ Get Started).
  - Universal back gesture/key navigation (`SystemBackHandler`) with tab stack history fallback.
- **Desktop Runtime Configuration**:
  - Default desktop window initialized to a centered mobile viewport (`412.dp x 860.dp`).

---

## 3. What is Remaining (Next Deliverables)

The table below breaks down the remaining scope according to the project specification (TRD & PRD):

| Area | Component | Description | Status |
|---|---|---|---|
| **Nahw (Syntax)** | Farasa Sidecar | REST/Docker wrapper for Farasa POS and dependency parser | Pending |
| | Dependency Mapper | Map parser relations to the 7 Quranic syntactic roles | Pending |
| | Nahw Endpoints | `POST /nahw/parse` (free text) & `GET /nahw/verse/{id}` (gold corpus lookup) | Pending |
| | Nahw UI Wiring | Connect `NahwResultScreen` to display color-coded dependency trees and i'rab legend | Pending (Mock UI ready) |
| **AI Tutor** | Gemini Integration | Google Gemini API with prompt engineering grounded in verified Quranic references | Pending |
| | Guardrails & Verification | Validate all cited `surah:ayah` references against DB before responding to user | Pending |
| | Tutor Chat Streaming | SSE / WebSockets / streaming text response for conversational tutor | Pending |
| | Tutor UI Wiring | Connect `TutorChatScreen` with quick-prompt chips and verse cross-navigation | Pending (Mock UI ready) |
| **Adaptive Learning** | Assessment Engine | Placement test and lesson player both run end-to-end on `Mock` data; scoring is real. Needs the backend to replace the data source | Data done, API pending |
| | Prerequisite Graph | Lesson unlock engine (`LessonNode` graph) | Pending |
| | Lesson Content | Backend lesson repository (Sarf & Nahw progression modules) | Pending |
| | Learn UI Wiring | Connect `HomeLearnScreens` (path map, lesson player, quiz, complete) | Pending (Mock UI ready) |
| **Infra & Optimization** | Redis Cache | Redis caching for Quran/morphology queries & IP rate limiting | Pending (Local dev uses in-memory) |
| | TTS / Audio | Ayah audio recitation player integration (if prioritized) | Optional |
| | Evaluation Scripts | Formal evaluation benchmark scripts for Sarf (vs corpus) and Nahw | Pending |

---

## 4. Suggested Immediate Next Steps

1. **Milestone 4 — Nahw Endpoints & Farasa Parser**:
   - Implement `GET /api/v1/nahw/verses/{verse_id}` to serve the ingested `nahw_annotations` table.
   - Wire `NahwResultScreen` in Compose to visualize color-coded i'rab breakdown directly from the database.
2. **Milestone 4 — AI Tutor (Gemini Integration)**:
   - Configure Gemini API key in `backend/app/core/config.py`.
   - Implement `/api/v1/tutor/chat` with strict Quranic retrieval-augmented verification.
   - Connect `TutorChatScreen` for conversational Q&A.
3. **Milestone 5 — Adaptive Lesson Graph**:
   - Define lesson data schema and diagnostic placement questions to replace mock learning path data.
