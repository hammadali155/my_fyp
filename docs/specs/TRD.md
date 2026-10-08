# Technical Requirements Document (TRD)

## AI-Powered Classical Arabic & Quranic Learning Platform

**Version:** 1.0  
**Date:** 2026-03-25  
**Author:** Meher Ali (FA23-BCS-059)  
**Status:** Draft

---

## 1. System Overview

A three-tier architecture: a single Kotlin Multiplatform (Compose Multiplatform) client shared across Android, iOS, Desktop, and Web, a centralized FastAPI REST backend, and specialized AI/NLP services. All data flows through a single REST API so every platform shares identical business logic in one Kotlin codebase.

```
┌──────────────────────────────┐
│  Kotlin Multiplatform Client │
│  Compose Multiplatform UI    │
│  Android · iOS · Desktop ·   │
│  Web (Wasm)                  │
└─────────────┬────────────────┘
              │
              ▼
        ┌─────────────────────┐
        │   FastAPI REST API   │
        │   (Single backend)   │
        └──────┬────────┬─────┘
               │        │
        ┌──────┴───┐  ┌┴──────────┐
        │PostgreSQL│  │   Redis   │
        │ (relational) │ (cache) │
        └──────┬───┘  └──────────┘
               │
        ┌──────┴─────────────────────────┐
        │      AI / NLP Services         │
        │  CAMeL Tools │ Farasa │ Gemini │
        └──────┬─────────────────────────┘
               │
        ┌──────┴─────────┐
        │   Quran Data    │
        │ Quran.com API + │
        │ corpus.quran.com│
        └─────────────────┘
```

---

## 2. Technology Stack

### 2.1 Frontend

| Layer | Technology | Version | Notes |
|-------|-----------|---------|-------|
| Shared UI (all platforms) | Kotlin Multiplatform + Compose Multiplatform | Kotlin 2.x / Compose 1.7+ | One shared UI module targets Android, iOS, Desktop (JVM), Web (Wasm) |
| Targets | Android, iOS, Desktop, Web (Wasm) | — | Target set matches the `kmptest/` spike structure |
| Navigation | Compose Navigation (JetBrains multiplatform) | latest | Multiplatform navigation |
| State / ViewModel | androidx.lifecycle viewmodel-compose | latest | Multiplatform ViewModel |
| HTTP Client | Ktor Client | 3.x | Shared engine per platform; interceptors for JWT |
| Serialization | kotlinx.serialization | latest | Generated DTOs shared with API |
| DI | Koin (multiplatform) | latest | Lightweight |
| Arabic Typography | Amiri / Noto Naskh Arabic bundled via Compose resources | — | Uthmanic-compatible fonts |

### 2.2 Backend

| Layer | Technology | Version | Notes |
|-------|-----------|---------|-------|
| Framework | FastAPI | 0.100+ | Async, auto-OpenAPI docs |
| Language | Python | 3.11 | |
| ORM | SQLAlchemy 2.0 | 2.x | Async SQLAlchemy |
| Migrations | Alembic | 1.x | Versioned schema |
| Validation | Pydantic | 2.x | Request/response models |
| Auth | PyJWT + python-bcrypt | latest | JWT access + refresh |
| Redis Client | redis-py | 5.x | Sessions, rate limiting, cache |
| MQ | (optional) Celery + Redis | — | For batch NLP jobs |

### 2.3 AI / NLP

| Tool | Purpose | Integration |
|------|---------|-------------|
| CAMeL Tools | Morphological analysis, root extraction, diacritization, POS | Python package `camel-tools` |
| Farasa | POS tagging, dependency parsing | Java jar / REST wrapper |
| MADAMIRA | Diacritization (backup/enhancement) | Java tool |
| Gemini 2.0 Flash | AI Tutor chatbot | Gemini REST API |
| corpus.quran.com dataset | Gold-standard morphological annotations | Static ingestion script |

### 2.4 Data

| Store | Purpose |
|-------|---------|
| PostgreSQL 15+ | Users, progress, SRS data, Quran corpus, lesson content, chat history |
| Redis 7+ | Session cache, SRS hot queue, rate-limit counters, NLP result cache |

### 2.5 Infrastructure

| Component | Technology |
|-----------|-----------|
| Web hosting | Vercel |
| API hosting | Google Cloud Run |
| Database | Managed PostgreSQL (e.g., Neon / Supabase / AWS RDS) |
| Cache | Managed Redis (e.g., Upstash / Redis Cloud) |
| CI/CD | GitHub Actions |
| Monitoring | Sentry + uptime monitoring |

---

## 3. Architecture Decisions

### 3.1 Single Backend for All Clients
**Decision:** One FastAPI service exposes versioned REST endpoints.
**Rationale:** Shared business logic; AI/NLP is Python-native; no BFF needed for scope.
**Alternative:** Node.js backend — rejected because CAMeL Tools is Python-only.

### 3.2 Compose Multiplatform Shared UI (KMP)
**Decision:** One shared Compose Multiplatform module serves Android, iOS, Desktop (JVM), and Web (Wasm). No per-platform UI forks.
**Rationale:** Write once, run everywhere in Kotlin; matches the validated `kmptest/` spike structure; shared UI, models, and Ktor API client eliminate cross-platform drift.
**Risk:** Compose Web (Wasm) is the youngest target — if it stalls, the Android/Desktop targets ship first and Web waits; no rework needed because UI is shared.

### 3.3 NLP as Internal Services, Not Separate Microservices
**Decision:** CAMeL Tools and Farasa run inside the FastAPI process or as lazy-loaded workers, not standalone services in v1.
**Rationale:** No need for independent scaling; smaller deployment surface.
**Upgrade path:** Extract to separate service if CPU contention becomes an issue.

### 3.4 Gold-Standard Corpus from corpus.quran.com
**Decision:** Pre-ingest the open dataset into PostgreSQL as the reference morphological store, rather than calling corpus.quran.com live.
**Rationale:** Reliability, speed (local SQL lookup beats external HTTP), and offline dev.

### 3.5 Sync NLP Over HTTP, Async for Batch
**Decision:** Single-word Sarf/Nahw requests are synchronous (user waits). Verse-level batch analysis (e.g., preparing learning-path lessons) runs in background jobs (Celery + Redis).
**Rationale:** Interactive features need immediate feedback; batch work doesn't.

---

## 4. API Design

Base URL: `/api/v1`

### 4.1 Authentication
| Method | Route | Description |
|--------|-------|-------------|
| POST | `/auth/register` | Create account (email, name, password) |
| POST | `/auth/login` | JWT access + refresh tokens |
| POST | `/auth/refresh` | Rotate refresh token |
| POST | `/auth/logout` | Revoke token(s) |
| GET | `/auth/me` | Current user profile |

### 4.2 Quran
| Method | Route | Description |
|--------|-------|-------------|
| GET | `/quran/surahs` | Surah list |
| GET | `/quran/surahs/{surah_id}` | Surah detail |
| GET | `/quran/surahs/{surah_number}/verses/{ayah_number}` | Single verse by surah:ayah with words + morphology |
| GET | `/quran/roots` | Roots ranked by occurrence count (min_count, pos_tag, surah_number filters; limit ≤ 500) |
| GET | `/quran/verses` | Paged verse list (surah_id, juz_number, page_number filters) |
| GET | `/quran/verses/{verse_id}` | Single verse with word-level data |
| GET | `/quran/search?q=` | Search: Arabic queries matched against normalized `text_imlaei`, Latin queries against `translation_en`; items carry `matched_field`; pagination capped at 50/page |

### 4.3 Sarf Engine
| Method | Route | Description |
|--------|-------|-------------|
| POST | `/morphology/analyze` | Body: `{"word": "..."}` → root, pattern, features, segmentation |
| GET | `/morphology/segment` | Clitic segmentation detail for a word |
| GET | `/morphology/forms` | Verb form information (Forms I–X) |
| GET | `/morphology/roots/{root}` | Quranic verses containing the root (concordance) |

> Note: the implemented module is mounted at `/morphology` (not `/sarf`). `/sarf/conjugate` is not implemented; conjugation tables are deferred.

### 4.4 Nahw Parser
| Method | Route | Description |
|--------|-------|-------------|
| POST | `/nahw/parse` | Body: `{"text":"...", "is_quranic": true}` → tokens with POS + dependencies + Nahw roles |
| GET | `/nahw/verse/{surah}:{ayah}` | Pre-analyzed annotation for a verse (from corpus) |

### 4.5 AI Tutor
| Method | Route | Description |
|--------|-------|-------------|
| POST | `/tutor/chat` | Body: `{"session_id":"...", "message":"..."}` → AI Tutor response |
| GET | `/tutor/sessions` | List user chat sessions |
| DELETE | `/tutor/sessions/{id}` | Delete history |

### 4.6 SRS
| Method | Route | Description |
|--------|-------|-------------|
| GET | `/srs/due` | Today's review cards (due) |
| POST | `/srs/review` | Submit rating per card (1=Again, 2=Hard, 3=Good, 4=Easy) |
| GET | `/srs/stats` | Streaks, counts, mastery summary |
| POST | `/srs/cards` | Add word to review (custom item) |
| DELETE | `/srs/cards/{card_id}` | Remove card |

> Note: per decision `docs/decisions/srs-design.md` (Option A), SRS uses a single
> `srs_cards` table + `srs_review_logs`, ratings 1–4 and state `graduated`;
> there are no `decks` and no `/srs/decks` endpoint in v1. FSRS is deferred.

### 4.7 Learning Path
| Method | Route | Description |
|--------|-------|-------------|
| POST | `/path/assess` | Submit onboarding assessment answers → placement |
| GET | `/path/plan` | Current personalized curriculum |
| GET | `/path/lessons` | Lesson list with lock state |
| GET | `/path/lessons/{id}` | Lesson content |
| POST | `/path/lessons/{id}/complete` | Mark lesson complete, trigger unlock logic |
| GET | `/path/progress` | Progress dashboard data |

### 4.8 Response Envelope
All responses wrap with `{ "ok": true, "data": ..., "error": null }`. Errors use standard HTTP codes with `{ "ok": false, "data": null, "error": { "code": "...", "message": "..." } }`.

---

## 5. Database Schema (High-Level)

Full schema in **Backend Schema** document. Entities:

- `users` — id, email, name, password_hash, level, created_at
- `refresh_tokens` — id, user_id, token_hash, expires_at, revoked
- `surahs` — id, number, name_ar, name_en, name_transliteration
- `verses` — id, surah_id, ayah_number, text_uthmani, text_imlaei, translation_en, translation_ur
- `words` — id, verse_id, position, token, diacritized, root, pattern, pos, morpheme_json
- `nahw_annotations` — id, verse_id, token_index, role, head_index, dep_type (from corpus)
- `lessons` — id, title, level, module, sequence, content_json
- `lesson_prerequisites` — lesson_id, requires_lesson_id
- `user_lessons` — user_id, lesson_id, status, completed_at, score
- `srs_cards` — id, user_id, word_id, item_type, front, back, hint, surah_number, ayah_number, state, ease_factor, interval_days, repetitions, lapses, due_date, last_reviewed_at
- `srs_review_logs` — id, card_id, user_id, rating, review_duration_ms, previous/new interval, previous/new ease_factor, reviewed_at
- `chat_sessions` — id, user_id, title, created_at
- `chat_messages` — id, session_id, role (user/assistant), content, created_at
- `assessment_attempts` — id, user_id, score, placed_level, completed_at

---

## 6. SRS Algorithm — SM-2 variant (as implemented)

Ratings are 1–4 and scheduling is server-authoritative
(`app/services/srs_service.py::_sm2_schedule`). Client sends only `{ card_id, rating }`.

### 6.1 Parameters
| Field | Initial | Update |
|-------|---------|--------|
| repetitions (n) | 0 | incremented on success in learning |
| ease_factor (EF) | 2.5 | clamp [1.30, 3.00] |
| interval_days | 0 | per rules below |
| state | `new` | `new` → `learning` → `review` → `graduated` |

### 6.2 Rating → Update Rules
| Rating | Value | State `new`/`learning` | State `review` | EF |
|--------|-------|------------------------|----------------|----|
| Again | 1 | → `learning`, interval 1d | → `learning`, interval 1d | EF −= 0.20 (floor 1.30) |
| Hard | 2 | interval = 1d (graduating), → `learning` | interval × 1.20, stays `review` | EF −= 0.15 |
| Good | 3 | interval = 1d (graduating); second success → `review`, 2d | interval × EF, stays `review` | EF unchanged |
| Easy | 4 | graduate immediately: 4d, → `review` | interval × EF × 1.30, stays `review` | EF += 0.10 (cap 3.00) |

EF adjustment in learning follows the SM-2 form `EF += 0.1 − (5−q)(0.08 + (5−q)·0.02)` with floor 1.30. Constants: graduating interval 1 day, easy graduating interval 4 days, easy bonus 1.30, hard multiplier 1.20, EF floor 1.30.

### 6.3 Algorithm Steps
1. Fetch `srs_cards` where `due_date <= now`, ordered by `due_date` ASC (oldest-first).
2. Present front → user recalls → reveal back (root, meaning, example).
3. User self-rates 1–4 (Again / Hard / Good / Easy).
4. Update EF, interval, repetitions, due_date, state per §6.2.
5. Append to `srs_review_logs` (with previous/new interval and EF, duration).
6. Update streak counters in `users` and gamification data.

> FSRS is explicitly deferred; see `docs/decisions/srs-design.md`.

---

## 7. NLP Integration Contracts

### 7.1 CAMeL Tools — Morphology
```python
from camel_tools.morphology.database import MorphologyDB
from camel_tools.morphology.analyzer import Analyzer

db = MorphologyDB.builtin_db()
analyzer = Analyzer(db)

analyses = analyzer.analyze(word)
# -> list of dicts with features: root, pattern, pos, asp, mod, gen, num, per
```

**Mapping to Nahw/Sarf model:**
- ``root`` → `words.root`
- ``pattern`` → `words.pattern`
- ``pos`` → `words.pos`
- verb tense/voice → `words.features_json`

### 7.2 Farasa — Dependency Parsing
Usage: send text to Farasa REST endpoint (wrap as sidecar), get:
```json
{
  "tokens": ["قَالَ", "اللَّهُ", ...],
  "tags": ["VERB", "NOUN", ...],
  "deps": [{"head": 1, "dep": "SUBJ"}, ...]
}
```
**Mapping to Nahw roles:**
- `SUBJ` → فاعل
- `OBJ` → مفعول به
- Copular constructions → مبتدأ / خبر
- `NMOD` / modifiers → نعت
- Circumstantial → حال

### 7.3 Gemini — AI Tutor Prompt Contract
System prompt (base):

```
You are an expert Classical Arabic (Nahw & Sarf) tutor for the Quranic learning platform.
Rules:
1. Answer all grammar questions in Classical Arabic terminology (فاعل، مفعول، مبتدأ، خبر، etc.) with English glosses for beginners.
2. Always ground answers in Quranic verses. Cite surah:ayah. Never invent a Quranic reference.
3. Match explanation depth to learner level (beginner/intermediate/advanced).
4. When a learner is wrong, correct gently and re-explain with the rule.
5. Keep answers under 200 words unless asked to elaborate.
```

Context injection: user profile (level, weak areas, recent lessons) + conversation history.

---

## 8. Data Ingestion Pipeline

### 8.1 Quranic Corpus Import (one-time)
Script: `scripts/ingest_quran.py`

1. Download verse text + translations from Quran.com API (or tanzil.net dataset).
2. Download corpus.quran.com dataset (TSV with tokens, roots, patterns, POS, morphology).
3. Normalize diacritics to Uthmanic standard.
4. Batch-insert into `surahs`, `verses`, `words`, `nahw_annotations`.
5. Validate: total words == 77,430; spot-check 1% against corpus.quran.com web UI.

### 8.2 Lesson Content Import
- Lessons authored as JSON (structure, exercises, quizzes) checked into repo `data/lessons/`.
- Prescriptive metadata: prerequisite lessons, level, module.

---

## 9. Rate Limiting & Caching

### 9.1 Rate Limits (Redis counters)
| Endpoint group | Limit |
|----------------|-------|
| Auth | 20 req/min/IP |
| Sarf/Nahw | 30 req/min/user |
| Tutor chat | 60 req/min/user |
| Quran lookup | 300 req/min/user |
| Global API | 1000 req/min/IP |

### 9.2 Cache Strategy
| Key | TTL | Purpose |
|-----|-----|---------|
| `quran:verse:{id}` | 24h | Verse + words JSON |
| `sarf:{word}` | 24h | Morphology analysis result |
| `nahw:{text-hash}` | 24h | Parse result |
| `srs:due:{user_id}` | 30s | Hot review queue snapshot |

---

## 10. Security Requirements

### 10.1 Authentication
- Passwords: bcrypt (cost 12), never stored plaintext
- Access token: JWT (HS256 or RS256), 15-min expiry
- Refresh token: opaque UUID stored hashed in `refresh_tokens`, 30-day expiry, rotation on use
- JWT claims: `sub` (user id), `iat`, `exp`, `type`

### 10.2 Authorization
- Role check middleware: `user` vs `admin`
- Resource ownership checks on all user-specific routes (SRS, chat, path)
- Admin-only: content management, user lookup

### 10.3 Input Validation
- Pydantic models for all request bodies
- Arabic text sanitization (strip control chars, normalize alef/hamza forms)
- SQL injection prevented via parameterized ORM queries
- No arbitrary HTML in stored content (render via sanitized Compose text components)

### 10.4 LLM Safety
- Prompt injection guard: user messages wrapped with instruction boundaries
- Output content filter: reject tutor responses containing fabricated Quranic references (verify surah:ayah against corpus before display)

---

## 11. Testing Strategy

### 11.1 Unit Tests
- SM-2 scheduler (all rating paths, interval/EF edge cases)
- Nahw role mapping (Farasa dep → classical term)
- Morphology feature mapping (CAMeL dict → model)
- Auth (token issue/refresh/revoke)
- Validation rules

### 11.2 Integration Tests
- Ingest pipeline correctness (word counts, normalization)
- API contract tests (OpenAPI schema ↔ client types)
- Redis cache invalidation

### 11.3 Evaluation Scripts
- `evaluate_sarf.py`: 500-word sample vs corpus.quran.com → accuracy/precision/recall
- `evaluate_tutor.py`: 50 conversation samples → expert Likert scores
- `evaluate_srs.py`: retention at 7/30-day vs control

### 11.4 E2E
- Shared UI flow tests: Compose UI tests in `commonTest` + Android instrumented tests (auth → sarf → srs → tutor)
- Web (Wasm): Playwright against the compiled web target for the same core flows
- iOS: shared test run on simulator via the KMP test runner

---

## 12. Deployment

### 12.1 Environments
| Env | URL | Purpose |
|-----|-----|---------|
| dev | localhost | Local development |
| staging | staging.<domain> | Integration testing |
| prod | <domain> | Public release |

### 12.2 CI/CD Pipeline (GitHub Actions)
1. Lint (ruff) + type check (mypy) + unit tests on push
2. Build FastAPI Docker image
3. Migrate DB (alembic upgrade) on deploy
4. Deploy API to Cloud Run, web to Vercel
5. Smoke test: health + auth + sarf endpoint

### 12.3 Environment Variables
```
DATABASE_URL, REDIS_URL, JWT_SECRET, JWT_REFRESH_SECRET,
GEMINI_API_KEY, CAMEL_DB_PATH, FARASA_URL,
QURAN_API_BASE, ALLOWED_ORIGINS, SENTRY_DSN
```

---

## 13. Performance Budgets

| Operation | Budget |
|-----------|--------|
| Auth (login) | 200ms |
| Quran verse lookup | 200ms |
| Sarf analyze (CAMeL cold) | 2s |
| Sarf analyze (warm/cached) | 100ms |
| Nahw parse verse | 3s |
| Tutor first token | 1.5s |
| SRS queue fetch | 150ms |
| Dashboard load | 500ms |

---

## 14. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| CAMeL Tools performance | High | Medium | Cache analyses; batch at ingest time |
| Farasa Java dependency | Medium | High | Wrap in sidecar REST; fallback to CAMeL parser |
| Gemini API cost/quota | Medium | Medium | Rate limits; caching; budget alerts |
| Farasa accuracy on Quranic | High | Medium | Use corpus.quran.com gold data for quranic verses; Farasa for free-text |
| corpus.quran.com license | Low | High | Verify license; cite source; educational use |
| Compose Web (Wasm) maturity | Medium | Medium | Android/Desktop ship first; Web is stretch target; shared UI means no rework |
| Quran text rendering bugs | Medium | High | Golden tests on RTL + diacritics rendering |

---

## 15. Open Technical Questions
1. Confirm Quran corpus license terms for redistribution.
2. Decide Madani vs Uthmanic script for base text.
3. Farasa service: bundle jar in repo vs Docker sidecar.
4. Gemini quota tier for production (free tier insufficient?).
5. CI minutes budget for GitHub Actions (self-host Docker runner?).