# Decision Memo: SRS Design — Keep, Migrate to Spec, or Migrate + FSRS

**Status:** Decided — Option A (keep current single-table design). Date: 2026-10-04.
**L6 completion audit:** 2026-11-24. The coverage tables below are authoritative for what is implemented, deferred, or not applicable.

## Background

TRD §6 + BackendSchema §3.4/§6 originally specified: `decks` → `cards` → `card_reviews`, SM-2 ratings 1–5, statuses `new/learning/review/mastered`, server-authoritative scheduling, deck-scoped due queries. The implemented code (`app/models/srs.py`, `app/services/srs_service.py`) differs: single `srs_cards` (with `item_type`: root/vocabulary/verse_fill_blank/grammar_rule) + `srs_review_logs`, ratings 1–4, state `graduated`, user-scoped directly on the card. The literature review recommends FSRS over SM-2 (~20–30% fewer reviews, personalization, `py-fsrs`/`FSRS-Kotlin` available).

## Option A — Keep current single-table design

- **Effort:** 0 days at decision time; spec docs aligned to code on 2026-10-04. L6 completion added mastery transitions, integrity checks and corpus-grounded card fields on 2026-11-24.
- **Migration risk:** None at decision time; the L6 integrity migration (`af458d94019b`) was verified upgrade → downgrade → re-upgrade on a scratch copy of the real DB.
- **Kotlin client effect:** None at decision time; L6 added corpus-derived fields to the existing `SrsCardDto` and surfaced the example ayah on the flashcard back.
- **FR coverage:** FR-SRS-01 (SM-2) ✓; FR-SRS-02 (Quranic flashcards) partial — root/pattern/POS/transliteration and example ayah are now sent from the corpus, audio remains absent; FR-SRS-03 (daily queue) partial — due-first ordering exists, forgetting-threshold priority and caps are deferred; FR-SRS-04 (mastery states) ✓ via `new/learning/review/graduated`; FR-SRS-05 (streaks/XP) ✓; FR-SRS-06 (custom decks) partial — `/decks` exists, full management is deferred.

## Option B — Migrate to spec's decks/cards/card_reviews + SM-2 (ratings 1–5)

- **Effort:** 3–5 days (models, Alembic migration + backfill, service rewrite, test rewrite, default deck seed).
- **Migration risk:** Medium; low real data loss (only Al-Fatiha seeded), but SM-2 edge-case regressions possible.
- **Kotlin client effect:** Moderate (deck_id, /srs/decks, ratings 1–5, graduated→mastered) — absorbed now since no client API code exists yet.
- **FR coverage:** All six FRs as written.

## Option C — B + FSRS

- **Effort:** 5–7 days (B + `py-fsrs`, scheduler swap, stability/difficulty columns, test rewrite).
- **Migration risk:** Medium-high; benefits need weeks of real data, unverifiable in a 30-user study.
- **Kotlin client effect:** Same as B optionally plus `FSRS-Kotlin` for offline.
- **FR coverage:** Violates FR-SRS-01's letter (says SM-2); needs PRD amendment.

## Addendum 2026-10-04

A `decks` table and `srs_cards.deck_id` were added (via Alembic `b8cfafcfbe10`),
marking a partial step toward Option B after all: decks group existing `srs_cards`,
but the single-table SM-2 scheduler, ratings 1–4, and `graduated` state are unchanged.
The `/srs/cards`, `/srs/due`, `/srs/review`, `/srs/stats` endpoints keep their
existing shapes; new deck endpoints live under `/decks`.

## Addendum 2026-11-24 — L6 SRS completion audit

Nothing in the SRS design or API specs is left implicit. Items marked **deferred**
are deliberate v1 omissions with the reason recorded here; they are not pending
accidental omissions. “Client today” means a currently routable Kotlin screen that
reads or could read the behaviour.

### Covered

| Behaviour | Status | Where / decision | Client today |
|---|---|---|---|
| Single `srs_cards` + `srs_review_logs`, `item_type`, ratings 1–4, server-authoritative SM-2 | Already implemented | `app/models/srs.py`, `app/services/srs_service.py` | Yes — `FlashcardScreen` rates 1–4 |
| `POST /srs/cards`, `GET /srs/due`, `POST /srs/review`, `GET /srs/stats`, `DELETE /srs/cards/{id}` | Already implemented | `app/api/v1/srs.py` | Yes — due, review, decks list; create/delete via API only |
| XP, UTC streak, badges on review | Already implemented | `ProgressService.apply_review_progress`, `users.last_activity_date` | Indirectly — profile/home show streak |
| Partial decks: `GET/POST /decks`, add single/bulk words, `DELETE /decks/{id}` | Already implemented | `app/api/v1/decks.py`, `app/services/deck_service.py` | Yes — `VocabularyScreen` lists decks |
| `graduated` is terminal mastery; interval > 21 days promotes `review → graduated` | Implemented L6 | `_sm2_schedule`, `_MASTERY_INTERVAL_DAYS = 21`; test `test_review_interval_above_21_days_marks_card_graduated` | No screen reads the mastered count today |
| `graduated` cards are excluded from the due queue and `due_now` | Implemented L6 | `SRSService.get_due_queue` / `get_stats`; tests in `backend/tests/test_srs_completion.py` | Yes — prevents mastered cards reappearing |
| DB `CHECK` on `srs_cards.state` and `srs_review_logs.rating` | Implemented L6 | Models plus migration `af458d94019b`; verified upgrade/downgrade/re-upgrade | No — data-integrity guarantee |
| Corpus-grounded response: root, pattern, POS, transliteration, example ayah text/reference/translation | Implemented L6 | `SRSCardResponse`, `SRSService._load_contexts`, migration-free; `SrsCardDto` and `FlashcardScreen` updated | Yes — `FlashcardScreen` showed `—` before |
| Supplied `word_id` must exist in `words`; omitted surah/ayah are derived from that word | Implemented L6 | `SRSService.create_card` returns 404 for unknown `word_id`; custom cards keep null corpus fields | No screen creates cards directly today |

### Deferred or not applicable

| Behaviour | Decision | Reason / current substitute | Client today |
|---|---|---|---|
| Audio on each flashcard | Deferred | No audio asset, player or field exists; PRD FR-SRS-02 remains only partially met | No audio UI |
| Review-history read endpoint / session summary | Deferred | `srs_review_logs` stores previous/new interval and EF, but there is no read route; `ReviewCompleteScreen` is still mock | Yes — would need a real summary |
| Deck rename/edit/archive, list cards in a deck, move/remove card between decks | Deferred | `/decks` is intentionally partial; no deck-management screen or route exists | No |
| Deck-scoped due queue / stats | Deferred under Option A | Due queue is user-scoped; `VocabularyScreen` shows per-deck counts but starts a global queue | Partial |
| Daily new-card limits, forgetting-threshold priority, ≤15 min / 50 cards acceptance | Deferred | Queue is `due_date ASC` with a limit; priority scoring and retention measurement need study data | No cap/priority UI |
| Suspend a card | Deferred | No column, state or endpoint; would need a schema change and a UI control | No |
| Undo last review | Deferred | Review log has no previous state/due/repetitions snapshot and undo would also have to reverse XP/streak | No |
| Edit card meaning/example overrides | Deferred | No update endpoint; custom `front`/`back` supplied at creation remain authoritative | No |
| Single-card duplicate add returns the existing card | Deferred | Bulk add skips duplicates; single create still returns the new card or 409 when a unique constraint applies | No screen calls create today |
| Full `decks`/`cards`/`card_reviews` schema, ratings 1–5, `/srs/decks`, `mastered` label | Not applicable — Option A rejected it | `graduated` is the terminal mastered state; the new `/decks` router is the agreed partial step | N/A |
| Redis hot queue `srs:due:{user_id}` | Deferred | Redis is optional and not deployed; SQLite/Postgres is canonical | No |
| Weak-area remedial injection into SRS | Deferred | Needs learning-path weak-area tracking and a corpus-grounded card generator | No |
| Retention ≥80% at 30 days / evaluation scaffold | Deferred research task | Cannot be measured before longitudinal usage data; no pass rate is claimed | No |
| Offline cached review queue | Deferred | Ktor client fetches live; no offline cache/reconciliation path exists | No |
| FSRS scheduler | Deferred | Would change the SM-2 contract in FR-SRS-01; needs real review data | No |
