# AGENTS.md

Guidance for AI agents (and humans) working in this repository. Read this first in every session.

## Project Overview

**Jawhar (جوهر): AI-Powered Classical Arabic & Quranic Learning Platform.** Final Year Project, COMSATS University Islamabad, Attock Campus.

Learners study Classical Arabic through the Quran. Core domains:

- **Sarf (morphology):** roots, patterns, verb forms I-X, conjugation, root occurrences.
- **Nahw (syntax):** verse and sentence parsing, grammatical roles (i'rab), dependency trees.
- **AI Tutor:** Gemini-powered chat grounded in verified Quranic references.
- **Vocabulary SRS:** spaced-repetition flashcards, streaks, XP.
- **Adaptive learning path:** assessment, lessons with prerequisites, weak-area tracking.

## Guardrails (non-negotiable)

- **Quranic accuracy is paramount.** A single diacritic error can change meaning. Never edit, regenerate or "fix" Quranic text, translations or annotations by hand. Anything touching the corpus must be validated against the source data before landing.
- **Never invent a Quranic reference.** Any `surah:ayah` produced by code or an LLM must be checked against the `verses` table.
- **Never invent library APIs.** For CAMeL Tools, Farasa, Gemini and similar, confirm function names against the installed package or official docs and run a small real call before building on it.
- **No secrets in git.** `.env`, `*.db` are gitignored; keep it that way. API keys live in `.env` only.
- Do not add code comments unless asked.
- Do not commit unless explicitly requested.

## Current State (update this section as work lands)

Done and tested:
- Auth: register, login, refresh, logout, me, profile update.
- Full Quran corpus ingested (2026-10-04): 114 surahs, 6,236 verses, 77,429 words, 77,429 nahw_annotations (0 verse-level word-count diffs vs EQTB).
- Quran read endpoints (surahs, verses, words, search, `/quran/surahs/{n}/verses/{m}`); verses list supports surah_id, juz_number, page_number filters; search normalizes Arabic (diacritic-insensitive) and reports `matched_field`.
- Morphology service: rule-based clitic segmentation, root lookup from the stored corpus, verb Forms I-X detection, root concordance.
- SRS: create card, due queue, review (SM-2 variant, ratings 1-4), stats, delete.
- `words` table extended with pattern/tense/voice/gender/number/person/features_json; `nahw_annotations` table populated from EQTB.
- Bookmarks: `bookmarks` table (user_id, verse_id, note, collection, timestamps; unique per user+verse) with POST create-or-update, GET list (?collection=), DELETE /{bookmark_id} — user-scoped.
- Decks: `decks` table + `srs_cards.deck_id`; GET/POST `/decks`, POST `/decks/{id}/words`, POST `/decks/{id}/words/bulk`, DELETE `/decks/{id}`; `scripts/seed_default_deck.py` seeds a per-user default deck from top-100 roots. Card text/gloss taken verbatim from the `words` table (words.translation_en backfilled from EQTB 2026-10-04).
- User progress: review transactions update `users.xp` (rating-scaled), `streak_days` and `last_review_date` (UTC; single source of truth via `compute_streak_update`); badges + user_badges added, 5 seeded badges, `GET /api/v1/progress/badges`.
- `/quran/roots`: roots ranked by occurrence count with min_count/pos_tag/surah_number filters and limit ≤ 500.
- CAMeL Tools installed as optional `nlp` extra (`uv sync --extra nlp`); `analyze_word` prefers corpus data, else CAMeL, else rule-based; response carries `source` (corpus|camel|rules); CAMeL calls memoized with an in-process LRU. `scripts/camel_smoke.py` exercises the analyzer.
- `POST /morphology/conjugate`: past/present/imperative for sound roots only; weak/hamzated/doubled roots return explicit `unsupported_reason`. Built from the existing VERB_FORMS_CATALOG (`fill_pattern` + `IMPERATIVE_PATTERNS`).
- `GET /morphology/word-family/{root}`: distinct lemmas grouped by pos_tag with counts and one real example verse each; `GET /morphology/patterns`: verb forms catalog + static noun patterns (`app/db/noun_patterns.py`) with example words resolved from the `words` table (null when absent — never invented).

Not done:
- ~~Full Quran data~~ — done 2026-10-04 (77,429 words ingested; the reference figure 77,430 counts a placeholder row).
- ~~`Word` model lacks pattern...~~ — added 2026-10-04, with migration.
- ~~No `nahw_annotations` table~~ — added and populated 2026-10-04.
- CAMeL Tools integration, Farasa sidecar, Nahw endpoints, AI Tutor, learning path, gamification, admin/CMS, notifications, Redis caching and rate limiting.
- Frontend still runs on hard-coded sample data; no API client yet.

## Repository Structure

```
my_fyp/
├── AGENTS.md
├── README.md                  # Kotlin Multiplatform project readme
├── backend/                   # FastAPI service (Python)
│   ├── app/
│   │   ├── main.py            # app factory, CORS, middleware, router mounting
│   │   ├── api/v1/            # routers: auth, quran, morphology, srs, health
│   │   ├── core/              # config, security, deps, middleware, logging
│   │   ├── models/            # SQLAlchemy models (user, quran, srs)
│   │   ├── schemas/           # Pydantic request/response models
│   │   ├── services/          # business logic, one service class per domain
│   │   └── db/                # session, base, seed_data
│   ├── alembic/               # migrations
│   └── tests/                 # pytest suite
├── scripts/                   # ingest_quran.py (currently seeds Al-Fatiha only)
├── shared/ androidApp/ iosApp/ desktopApp/ webApp/   # Kotlin Compose Multiplatform client
├── docs/
│   ├── specs/                 # PRD, TRD, BackendSchema, ImplementationPlan, AppFlow, UI-UX-Design
│   ├── proposal/ defense/ diagrams/ planning/
└── research/                  # papers, literature review, resource links
```

## Commands

Backend (run from `backend/`):
- Install: `uv sync` (add `--extra postgres` or `--extra redis` as needed)
- Migrate: `uv run alembic upgrade head`
- New migration: `uv run alembic revision --autogenerate -m "message"`
- Dev server: `uv run fastapi dev app/main.py` (docs at `http://localhost:8000/docs`)
- Test: `uv run pytest`
- Lint: `uv run ruff check`
- Typecheck: `uv run mypy app`
- Ingest corpus: `uv run python ../scripts/ingest_quran.py`

Client (run from repo root, Windows uses `kotlin.bat`):
- Build: `./kotlin build`
- Test: `./kotlin test`
- Run desktop: `./kotlin run -m desktopApp`

A change is done only when `pytest`, `ruff check` and `mypy app` all pass.

## Backend Conventions

Layering: **router (`api/v1`) -> service (`services`) -> models (`models`)**. Routers stay thin; logic lives in a service class constructed with the DB session.

- Every module starts with `from __future__ import annotations`.
- Routers: `APIRouter(prefix="/name", tags=["Readable Name"])`, a module logger `get_logger("api.name")`, explicit `response_model`, `status_code` and `summary` on each route. Inject `DbSession` and `CurrentUser` from `app.core.deps`.
- Services: class `NameService` with `__init__(self, db: AsyncSession)`. Raise `HTTPException` for not-found and permission errors. Always filter user data by `user_id`.
- Schemas: Pydantic v2 with `Field` constraints. Response models that map ORM rows set `model_config = {"from_attributes": True}`. Re-export new schemas in `schemas/__init__.py`.
- Models: SQLAlchemy 2.0 `Mapped`/`mapped_column`, inherit `TimestampMixin, Base`, export in `models/__init__.py` (Alembic imports `app.models`). Index foreign keys and common filters.
- Register new routers in `api/v1/api.py`.
- Schema changes always go through an Alembic migration; never hand-edit the database.
- Tests live in `backend/tests/test_<name>.py`, use the async `client`, `auth_headers`, `db_session` and `seed_quran_data` fixtures from `conftest.py` (in-memory SQLite), and call routes under `/api/v1`.

## Workflow for Agents

1. Read the relevant spec section before coding (see Specs below). Plan first for anything touching more than one file.
2. One module or endpoint per session. Keep diffs small; no unrelated refactors.
3. Write or update tests in the same change. Unit-test pure logic (schedulers, mappers) directly; test routes through the client.
4. Run the three checks before declaring done and report their results.
5. Use the `add-endpoint` skill for new routes.
6. After finishing, update **Current State** above and any changed commands.

## Specs

- `docs/specs/PRD.md`: features, requirements, acceptance criteria, scope.
- `docs/specs/TRD.md`: architecture, API list, SM-2 rules, NLP contracts, security, caching.
- `docs/specs/BackendSchema.md`: target database schema, SRS contract, Redis keys.
- `docs/specs/ImplementationPlan.md`: milestones and build order.
- `docs/specs/AppFlow.md`, `UI-UX-Design.md`: user flows and screens.
- `research/literature-review-summary.txt`, `research/important_links_to_explore.md`: tools and datasets.
- `docs/proposal/Arabic_Platform_Modules.pdf`: the 32-module list (broader than the PRD scope).

## Known Drift and Open Decisions

The specs and code disagree in places; decide, then align both:

- **SRS design:** Resolved 2026-10-04 (Option A, see `docs/decisions/srs-design.md`): specs were aligned to the code — single `srs_cards` table + `srs_review_logs`, ratings 1–4, `graduated` state. FSRS deferred.
- **Route names:** Resolved 2026-10-04: TRD updated to match the code — `/srs/due`, `/morphology/*`, `/quran/verses/{verse_id}`.
- **Scope:** the 32-module PDF includes a leaderboard and TTS audio, which the PRD marks out of scope; it lists 15 verb forms while the code has 10.
- **Ownership:** confirm with the project partner which backend parts are finished and who owns the next modules.
