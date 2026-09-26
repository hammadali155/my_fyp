# Application Flow Document

## AI-Powered Classical Arabic & Quranic Learning Platform

**Version:** 1.0  
**Date:** 2026-03-25  
**Author:** Meher Ali (FA23-BCS-059)  
**Status:** Draft

---

## 1. Flow Notation

- Rounded boxes = screen/view
- Diamonds = decision
- Arrow labels = action / API call
- Solid lines = app navigation
- Dotted lines = background/batch process

---

## 2. High-Level App Flow (State Diagram)

```
                          ┌────────────────────┐
                          │      Splash /       │
                          │   App Boot         │
                          └─────────┬──────────┘
                                    │ token present?
                          ┌─────────┴─────────┐
                          ▼                   ▼
                    ┌──────────┐        ┌────────────┐
                    │ Dashboard│◄───────│   Auth      │
                    │ (Home)   │        │  Login/Reg │
                    └────┬─────┘        └────────────┘
                         │ has onboarding?
                  ┌──────┴───────┐
                  ▼              ▼
            ┌──────────┐   ┌──────────────────┐
            │  Main App│   │   Onboarding      │
            │  (Learn/ │   │   → Assessment    │
            │  Review/ │   │   → Level place   │
            │  Tutor)  │   └──────────────────┘
            └──────────┘
```

---

## 3. Auth Flow

```
[Register] ──POST /auth/register──▶ [Verify email link] ──▶ [Login]
[Login] ──POST /auth/login──▶ {access, refresh} stored secure
   │
   ├─▶ access valid? ──▶ [Main App]
   └─▶ access expired? ──▶ POST /auth/refresh ──▶ new access ──▶ [Main App]
        └─ refresh expired/revoked ──▶ [Login screen]

[Logout] ──POST /auth/logout──▶ revoke refresh ──▶ clear local tokens ──▶ [Splash]
```

**Decisions:**
- If refresh valid → silent re-auth, no login prompt
- If refresh invalid → force login, clear cached SRS queue

---

## 4. Onboarding & Assessment Flow

```
[Welcome] ──Tap "Start"──▶ [Language select AR/EN]
   │
   └─▶ [Goal select: Understand Quran | Grammar | Vocab]
        └─▶ [Quick screen (3 q)] ── score < ? ──▶ [Full assessment: 20 q]
                                        │
                                        └─▶ [Show result: Level placed]
                                             └─▶ [Generate learning path]
                                                  └─▶ [Dashboard: view plan]
```

- Assessment answers batched as one `POST /path/assess`
- Placement determines initial level and which lessons unlock
- User can re-take assessment anytime (flag weak areas)

---

## 5. Daily Learning Loop (Habit Flow)

```
                      ┌─────────────────────────────────────┐
                      │      Morning Check-in              │
                      │  Dashboard: streak + due count     │
                      └──────────────────┬──────────────────┘
                                         │ "Start Review"
                                         ▼
                              ┌──────────────────────┐
                              │   SRS Review queue    │
                              └──────────┬───────────┘
                                         │ each card:
                              ┌──────────┴──────────┐
                              ▼                     ▼
                        [Show word]         [Reveal back]
                              │                     │
                              └─────────┬───────────┘
                                        ▼
                              ┌──────────────────┐
                              │  Rating UI       │
                              │ Again/Hard/Good/ │
                              │ Easy            │
                              └───────┬──────────┘
                                      ▼
                           POST /srs/review
                                      │
                              update SM-2 state
                          ┌───────────┴────────────┐
                          │ queue empty?            │
                          ▼                        ▼
                   ┌────────────┐         ┌──────────────────┐
                   │ Celebrate  │         │ Done for today    │
                   │ (streak)   │         │ ──▶ Tutor ask?    │
                   └────────────┘         │ ──▶ Next lesson?  │
                                          └──────────────────┘
```

**Decision:** After SRS, user chooses next activity: continue lesson, analyze a new verse, or chat with tutor.

---

## 6. Sarf Analysis Flow

```
[Input: Arabic word] ──Tap Analyze──▶ POST /sarf/analyze
        │
        ├─▶ cached?──▶ return from Redis
        ├─▶ validate input (Arabic normalization)
        ├─▶ run CAMeL Tools analyzer
        ├─▶ map features (root, pattern, POS, tense, voice, gen, num)
        └─▶ cache result 24h
                │
                ▼
[Result view: root, pattern, features, conjugation table]
        │
        ├─▶ [Show Quranic occurrences]─▶ GET /sarf/{root}/occurrences
        ├─▶ [Add to SRS deck]─────▶ POST /srs/cards
        └─▶ [Send to Nahw]────────▶ prefill sentence parse
```

**Error handling:** invalid Arabic → inline validation message; CAMeL no analysis → "not found", suggest alternate spelling.

---

## 7. Nahw Parse Flow

```
[Input: verse (from corpus) OR free text] ──Parse──▶ POST /nahw/parse
        │
        ├─▶ Quranic verse? ──▶ lookup gold annotation from `nahw_annotations`
        ├─▶ free text? ──▶ run Farasa (POS + dep parse)
        │                   └─▶ map SoS roles → Nahw terms
        ├─▶ render tokens with color + labels
        │
        ▼
[Annotated verse view]
   ├─▶ tap word ──▶ [Detail sheet: POS, i'rab, root, role]
   ├─▶ toggle dependency arrows overlay
   ├─▶ [Ask Tutor] ──▶ prefill tutor context with verse
   └─▶ [Add words to SRS] ──▶ multi-select ──▶ POST /srs/cards (batch)
```

---

## 8. AI Tutor Chat Flow

```
[Chat screen open] ──▶ GET /tutor/sessions ──▶ list previous / new session
   │
   ▼
[User sends message] ──▶ POST /tutor/chat {session_id, message}
   │
   ├─▶ build payload: system prompt + profile + history + message
   ├─▶ call Gemini API (stream)
   │    └─▶ safety guard: verify any surah:ayah cited IS in corpus
   ├─▶ stream response tokens to UI (SSE)
   └─▶ persist user + assistant messages
   │
   ▼
[Response rendered w/ tappable verse chips]
   ├─▶ tap verse ──▶ [Verse annotation]
   ├─▶ quick chips: "Quiz me" / "Explain a term" / "Give next lesson"
   └─▶ export / clear session
```

**Streaming:** use SSE or websocket; show typing indicator; keep UI responsive.

---

## 9. Lesson / Learning Path Flow

```
[Learning Path map] ──▶ GET /path/plan
   │
   ▼
[Lesson card (open → locked → complete)]
   │
   ├─▶ unlocked? ──▶ GET /path/lessons/{id} ──▶ [Lesson Player]
   │                                        │
   │     [Content: theory, examples, quiz]  │
   │        │                               │
   │        ├─▶ exercise answer ──▶ validated ──▶ feedback + score
   │        ├─▶ complete lesson ──▶ POST /path/lessons/{id}/complete
   │        │                         └─▶ unlock next lesson(s)
   │        └─▶ add new words to SRS ──▶ queue
   │
   └─▶ weak area detected? ──▶ inject remedial review card into SRS
```

---

## 10. Vocabulary / Deck Management Flow

```
[Dashboard ─ Vocabulary]
   ├─▶ My decks (new/learning/review/mastered counts)
   ├─▶ Create custom deck
   ├─▶ Add word (from Sarf result / Nahw verse / tutor)
   ├─▶ Edit card (meaning overrides, example)
   ├─▶ Delete / archive deck
   └─▶ [Start session] ──▶ SRS Review Flow
```

**Card states:** New → Learning (repetitions 0-2) → Review (interval), → Mastered (interval > 21d), with `status` transitions handled by SM-2 rules.

---

## 11. Cross-Screen Data Handoffs

| From | To | Handoff |
|------|----|---------|
| Sarf result | SRS | root, pattern, word → `POST /srs/cards` |
| Nahw annotation | Tutor | verse id + word indices → prefill context |
| Tutor verse chip | Nahw | surah:ayah → `GET /nahw/verse` |
| Lesson complete | SRS | new words auto-added |
| Lesson complete | Path | unlock chain evaluation |
| SRS weak rating | Path | weak areas feed remedial injection |

---

## 12. Edge Cases & Error Flows

| Scenario | Behavior |
|----------|----------|
| User opens app offline | Show cached dashboard + cached review queue; queue actions offline (post on reconnect if implemented) |
| Quran.com API down | Use pre-ingested local corpus; no live dependency in v1 |
| Gemini quota exceeded | Graceful fallback: show canned grammar FAQ response; retry with backoff |
| Farasa service down | Nahw free-text shows "service unavailable"; Quranic verses still use gold corpus |
| Invalid Arabic input | Normalize (alef/hamza/ta-marbuta), show suggestion, never crash |
| Duplicate card add | Dedup by (user, deck, word_id); return existing card |
| Assessment interrupted mid-way | Resume from last answered question; partial progress saved |
| Rate limit hit | 429 response → user-friendly message + retry-after hint |

---

## 13. Seed / Initial Data Flow

```
scripts/ingest_quran.py (run once at setup)
   │
   ├─▶ download verse text + translations ──▶ populate surahs, verses
   ├─▶ download corpus.quran.com dataset ──▶ populate words, nahw_annotations
   │
   fallback: bundle a snapshot JSON in repo for offline dev
   validation: word count = 77,430; sample checks vs corpus web
```

---

## 14. Flow Review Checklist

- [ ] Auth silent-refresh path correct
- [ ] Onboarding never forced on returning users
- [ ] SRS queue respects due-date ordering and streak updates
- [ ] Sarf/Nahw caching (24h) avoids repeated NLP cost
- [ ] Tutor never fabricates Quranic references
- [ ] Every screen reachable; no dead ends (e.g., locked lesson explains how to unlock)
- [ ] All handoffs in §11 implemented end-to-end
- [ ] Error flows in §12 documented in code comments