# Decision Memo: SRS Design — Keep, Migrate to Spec, or Migrate + FSRS

**Status:** Decided — Option A (keep current single-table design). Date: 2026-10-04.

## Background

TRD §6 + BackendSchema §3.4/§6 originally specified: `decks` → `cards` → `card_reviews`, SM-2 ratings 1–5, statuses `new/learning/review/mastered`, server-authoritative scheduling, deck-scoped due queries. The implemented code (`app/models/srs.py`, `app/services/srs_service.py`) differs: single `srs_cards` (with `item_type`: root/vocabulary/verse_fill_blank/grammar_rule) + `srs_review_logs`, ratings 1–4, state `graduated`, user-scoped directly on the card. The literature review recommends FSRS over SM-2 (~20–30% fewer reviews, personalization, `py-fsrs`/`FSRS-Kotlin` available).

## Option A — Keep current single-table design

- **Effort:** 0 days code; spec docs aligned to code (done 2026-10-04).
- **Migration risk:** None; SRS tests already pass.
- **Kotlin client effect:** None; DTOs unchanged.
- **FR coverage:** FR-SRS-01 (SM-2) ✓; FR-SRS-02 (Quranic flashcards) ✓ via `surah_number`/`ayah_number`/front/back fields; FR-SRS-03 (daily queue) ✓; FR-SRS-04 (mastery states) ✓ via `new/learning/review/graduated`; FR-SRS-05 (streaks/XP) partial; FR-SRS-06 (custom decks) scoped to `item_type` tags instead of decks — accepted trade-off.

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
