# Implementation Plan

## AI-Powered Classical Arabic & Quranic Learning Platform

**Version:** 1.0  
**Date:** 2026-03-25  
**Author:** Meher Ali (FA23-BCS-059)  
**Status:** Draft

---

## 1. Goals & Scope

Deliver a working MVP (Month 4), Beta (Month 5), and Release Candidate (Month 6) per the PRD release criteria, using the stack in the TRD and the schema in BackendSchema.md.

**In-scope (v1.0):** auth, Quran corpus ingestion, Sarf engine, Nahw parser, SRS (SM-2), AI Tutor, learning path + assessment, shared KMP client (Android / iOS / Desktop / Web), evaluation scripts.

**Out-of-scope (v1.0):** teacher dashboard, live tutoring, tajweed/audio recitation, social features, balaghah module, multiple qira'at.

---

## 2. Milestones & Phases

| Phase | Window | Deliverables | Exit Criteria |
|-------|--------|--------------|---------------|
| M1 Foundation | Month 1 | Repo scaffold, DB schema, ingestion, auth, CI | 1,000 verses ingested; auth works on the KMP client |
| M2 SRS Core | Month 2 | SM-2 engine, card review flow, streak, dashboard | SRS unit tests pass; beta UI review |
| M3 Sarf Engine | Month 3 | CAMeL integration, analyzer, occurrences, UI | Accuracy ≥ 90% on 500-word eval set |
| M4 Nahw + Tutor | Month 4 | Farasa parse, annotation UI, Gemini Tutor | Nahw accuracy ≥ 85%; tutor expert-rated ≥ 4.0 |
| M5 Adaptive Path + Mobile | Month 5 | Assessment, curriculum unlock, RN mobile | Mobile builds pass; learning-path e2e pass |
| M6 Eval & Polish | Month 6 | 30-user study, performance tuning, docs, demo | All PRD release criteria met |

---

## 3. Work Breakdown (M1)

### M1 — Foundation
| # | Task | Dep | Est. | Owner |
|---|------|-----|------|-------|
| 1 | Monorepo scaffold: `backend/`, `client/` (KMP), `scripts/`, `data/` | — | 0.5d | me |
| 2 | FastAPI app skeleton + config + health check | 1 | 1d | me |
| 3 | PostgreSQL schema via Alembic (all tables) | 1 | 2d | me |
| 4 | Auth: register/login/refresh/logout + JWT + bcrypt | 3 | 2d | me |
| 5 | Quran ingestion script (verses, words, annotations) | 3 | 2d | me |
| 6 | Quran read endpoints (surahs, verses, words, search) | 5 | 1d | me |
| 7 | Redis wiring + rate limiting middleware | 2 | 1d | me |
| 8 | KMP client scaffold (shared `client/` Compose Multiplatform: androidApp / iosApp / desktopApp / web target) | 1 | 1d | me |
| 9 | Auth screens + token handling (shared client) | 4 | 2d | me |
| 10 | CI (ruff, mypy, pytest, build) | 2 | 1d | me |

**M1 MVP demo:** user registers, logs in, browses surahs/verses, sees word morphology from corpus.

### M2 — SRS Core
| # | Task | Dep | Est. | Owner |
|---|------|-----|------|-------|
| 11 | SM-2 scheduler service + unit tests | 3 | 2d | me |
| 12 | Deck/card endpoints (create, add, review, stats) | 11 | 2d | me |
| 13 | SRS review UI (shared Compose) | 12 | 2d | me |
| 14 | Streak + XP + badges logic | 12 | 1d | me |
| 15 | Dashboard screen (streak, due count, continue) | 14 | 2d | me |
| 16 | Seed default Quranic vocab deck | 13 | 1d | me |
| 17 | SRS retention evaluation scaffolding | 13 | 1d | me |

**M2 MVP demo:** add words to deck, get daily queue, review with ratings, streak visible.

### M3 — Sarf Engine
| # | Task | Dep | Est. | Owner |
|---|------|-----|------|-------|
| 18 | CAMeL Tools install + analyzer service | 7 | 3d | me |
| 19 | Feature mapping (root/pattern/POS/tense/voice) | 18 | 1d | me |
| 20 | `/sarf/analyze` + `/sarf/conjugate` endpoints + cache | 19 | 2d | me |
| 21 | Root occurrences endpoint (corpus-backed) | 6 | 1d | me |
| 22 | Sarf UI (shared Compose): input → result → conjugation table | 20 | 3d | me |
| 23 | Sarf accuracy eval script vs corpus.quran.com | 21 | 2d | me |
| 24 | CAMeL batch precompute script (cache all Quranic words) | 20 | 1d | me |

**M3 MVP demo:** type any word → root, pattern, features, conjugation, Quranic occurrences.

### M4 — Nahw + Tutor
| # | Task | Dep | Est. | Owner |
|---|------|-----|------|-------|
| 25 | Farasa sidecar (Docker/REST wrapper) | 7 | 3d | me |
| 26 | Dep-parser → Nahw role mapper | 25 | 2d | me |
| 27 | `/nahw/parse` free-text + `/nahw/verse` gold lookup | 26 | 2d | me |
| 28 | Nahw annotation UI (color-coded, legend, detail sheet) | 27 | 4d | me |
| 29 | Gemini integration: /tutor/chat streaming + safety guard | 7 | 3d | me |
| 30 | Tutor chat UI (streaming, quick chips, verse chips) | 29 | 3d | me |
| 31 | Nahw + tutor evaluation scripts with expert rubric | 28,30 | 2d | me |

**M4 MVP demo:** parse a verse with color-coded roles; chat with tutor; verse chips route to annotation.

### M5 — Adaptive Path + Mobile
| # | Task | Dep | Est. | Owner |
|---|------|-----|------|-------|
| 32 | Assessment bank + placement logic | 10 | 2d | me |
| 33 | Curriculum unlock engine (prerequisite graph) | 32 | 2d | me |
| 34 | Learning path map UI | 33 | 3d | me |
| 35 | Lesson player (content JSON, exercises) | 34 | 3d | me |
| 36 | Weak-area tracking + remedial injection into SRS | 33 | 2d | me |
| 37 | KMP mobile targets polish: iOSApp wiring + signing config + shared API client (Ktor) | 10 | 2d | me |
| 38 | Mobile bottom-tab nav + dashboard + review + tutor screens | 37,30,15 | 5d | me |
| 39 | RTL font bundling across all targets | 38 | 1d | me |

**M5 MVP demo:** assessment places learner; lessons unlock; Android + iOS apps mirror desktop/web flows.

### M6 — Evaluation & Polish
| # | Task | Dep | Est. | Owner |
|---|------|-----|------|-------|
| 40 | 30-user study (pretest → 2wk usage → posttest) | 39 | 5d | me |
| 41 | Performance tuning (queries, NLP caching) | 39 | 2d | me |
| 42 | Security pass (auth, rate limits, secrets) | 41 | 2d | me |
| 43 | Accessibility + RTL golden tests | 42 | 1d | me |
| 44 | Deploy staging → prod (Cloud Run + Vercel) | 43 | 2d | me |
| 45 | FYP report + defense demo prep | 44 | 3d | me |

---

## 4. Repository Layout

```
fyp/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app factory
│   │   ├── api/v1/            # routers (auth, quran, sarf, nahw, tutor, srs, path)
│   │   ├── core/              # config, security, deps
│   │   ├── models/            # SQLAlchemy models (mirror schema doc)
│   │   ├── schemas/           # Pydantic request/response
│   │   ├── services/          # sm2.py, camel_service.py, farasa_service.py, gemini.py, ingest.py
│   │   └── db/                # session, base
│   ├── alembic/               # migrations
│   └── tests/                 # unit + integration + eval scripts
├── client/                     # KMP + Compose Multiplatform (all platforms)
│   ├── shared/                 # shared UI (App.kt), models, Ktor API client, theme
│   │   ├── src/commonMain/     # Compose UI + API client (Auth/Sarf/Nahw/SRS/Tutor/Path)
│   │   ├── src/androidMain/    # Android entry
│   │   ├── src/iosMain/        # iOS entry
│   │   ├── src/jvmMain/        # Desktop entry
│   │   └── src/jsWasmMain/     # Web (Wasm) entry
│   ├── androidApp/             # Android app module
│   ├── iosApp/                 # iOS app module
│   ├── desktopApp/             # Desktop app module
│   ├── gradle/libs.versions.toml
│   └── build.gradle.kts
├── scripts/
│   ├── ingest_quran.py
│   ├── precompute_camel.py
│   ├── evaluate_sarf.py
│   ├── evaluate_tutor.py
│   └── evaluate_srs.py
├── data/
│   ├── corpus_snapshot/        # seed JSON snapshots (dev offline)
│   ├── lessons/                # authored lesson JSON
│   └── assessment_bank.json
└── docs/specs/                 # this and sibling docs
```

---

## 5. Build Ordering Rationale

1. **Foundation first** — no feature ships until CI + schema + auth exist.
2. **SRS before Sarf** — vocab is the most self-contained module; proves auth/data flow early, delivers a usable product for the Month 2 milestone.
3. **Sarf before Nahw** — shares CAMeL ecosystem; Sarf is the simpler surface to validate accuracy first.
4. **Tutor after Nahw** — tutor cites verses/analysis that depend on Nahw output.
5. **Mobile targets after Desktop/Android stabilize** — shared Compose UI + API client mean adding iOS packs little rework; avoids double-build churn.
6. **Evaluation runs continuously from M2** — scaffolding exists early so data accumulates honestly.

---

## 6. Definition of Done

Each task is done when:
- Code implemented per TRD conventions
- Unit/integration test added where spec has non-trivial logic (SM-2, mappers, unlock engine)
- `ruff check`, `mypy`, `pytest` pass locally
- Feature manually exercised in the desktop/Android client (and iOS after M5) happy + error paths
- No new secrets in repo; env vars documented

---

## 7. Verification & Commands (to be recorded in AGENTS.md once stable)

| Action | Command |
|--------|---------|
| Lint | `cd backend && ruff check .` |
| Type check | `cd backend && mypy app` |
| Test | `cd backend && pytest` |
| DB migrate | `cd backend && alembic upgrade head` |
| Ingestion | `python scripts/ingest_quran.py` |
| Run API (dev) | `cd backend && uvicorn app.main:app --reload` |
| Run desktop client (dev) | `cd client && ./gradlew :desktopApp:run` |
| Run Android client (dev) | `cd client && ./gradlew :androidApp:installDebug` |
| Run web target (dev) | `cd client && ./gradlew :shared:wasmJsRun` (or `:shared:jsBrowserDevelopmentRun`) |

---

## 8. Dependencies & Risks

| Risk | Mitigation | Triggers review |
|------|-----------|-----------------|
| CAMeL model download blocked | Vendor models in `data/`; document offline path | M3 start |
| Farasa Java integration friction | Docker sidecar isolated; CAMeL parser fallback | M4 start |
| Gemini quota/cost in eval | Cache responses; budget alert; canned-lite fallback | M4 |
| corpus.quran.com licensing | Verify before ingestion; keep source attribution | M1 ingestion |
| Compose Web (Wasm) maturity | Ship Android/Desktop first; Web is the stretch target; shared UI means no rework | M5 |
| iOS toolchain access (Xcode/Mac) | If no Mac available, iOS target compiles later; Android + Desktop carry the demo | M5 |
| 30-user recruitment | Start outreach in M4; COMSATS + GDGoC lists | M5 |

---

## 9. Outstanding Questions for Human Partner

Before M1 starts, confirm:
1. **Repos/branching:** work in this repo (`fyp/`) with `backend/`, `client/`, etc., or separate repos?
2. **Deploy targets:** staging + prod on Cloud Run/Vercel as stated, or local-only for now?
3. **Client targets:** for the defense demo, which targets must work — Desktop + Android only, or iOS + Web (Wasm) too (requires Mac toolchain)?
4. **License/legal:** confirm permission to ingest and distribute the corpus.quran.com dataset locally in the app.
5. **Admin tooling:** any need for an admin panel for lesson content, or is checked-in JSON sufficient for v1?
6. **Single or paired developer:** does anything demand a second implementer for Month 5-6, or is solo work the plan?

---

## 10. Sign-off
- **Plan author:** Meher Ali (FA23-BCS-059)
- **Reviewers:** Supervisor
- **Status:** Awaiting answers to §9 before month-1 execution.