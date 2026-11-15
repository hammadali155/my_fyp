# Branch: feat/nahw — Nahw (syntax) module

Base: `dd55ad0` (master, includes PR #1 sarf-eval-lemma-remap).

## Context

The parked work from `5cbba79` (`backup/nahw-pre-rebase`, and `stash@{0}`) was
restored onto this branch intact (verified: the five nahw files are byte-identical
to that commit). It already lands part of the approved N1 plan.

## Ledger — what the approved plan wanted vs what exists

| # | Plan step | State |
|---|-----------|-------|
| 1 | NOTICE: EQTB attribution (CC BY 4.0), authors from Mendeley record | **DONE** (authors fetched from the Mendeley record) |
| 2 | Migration: `sentence_index` on `nahw_annotations` | **DONE** (`ab2e22cddb71`, + composite index) |
| 3 | Backfill script: word-level `head_index` from `ref_token_id`, `sentence_index`, Arabic `irab` (+verb moods), validation report | **DONE** (pure derivation + script; 77,429/77,429 updated, 0 mismatches) |
| 4 | `GET` verse annotations endpoint + service + tests | **DONE** (slash route `/nahw/verse/{surah}/{ayah}`) |
| 5 | `POST /nahw/parse`: corpus gold lookup first | **DONE**; free-text path calls a Farasa sidecar that does not exist → 503 |
| 6 | Role → `role_key` conservative mapping + unit tests | **DONE** (extended 2026-10-26: 98.97% covered, 35 keys; `tests/test_nahw_roles.py`) |
| 7 | Docs (AGENTS.md / TRD) + optional KMP client wiring | **PARTIAL** (AGENTS.md + TRD aligned; KMP client not wired) |
| 8 | Deferred: Redis cache/rate limit, free-text Farasa, expert-rubric eval | tracked, not built |

## Deviations from the plan to resolve

- **Route shape**: parked work uses `/nahw/verse/{surah}/{ayah}` (slash) and
  documents that in AGENTS.md. The TRD wrote `/nahw/verse/{surah}:{ayah}`.
  Keeping the slash form (consistent with `/quran/surahs/{n}/verses/{m}`) and
  aligning the TRD is the smaller, more consistent change.
- **`is_quranic` flag**: resolved 2026-10-25 — it now gates the corpus. Text
  declared Quranic that is not in the corpus returns `404` instead of being sent
  to Farasa, so a claimed Quranic string is never machine-parsed as free text.
- **Free-text**: still no parser installed. The 503 path is honest. Q1(a).
- **Cross-verse `head_index` (resolved 2026-10-26)**: EQTB sentences may span
  verses (838 of 11,693 sentences, 1,064 cross-verse head edges, 195 rows whose
  `head_index` exceeds their own verse's word count). `head_index` is the head's
  EQTB word position, so a head is now located by
  `(head_surah_number, head_ayah_number, head_index)`; both columns are null
  whenever `head_index <= 0`. Migration `ce4c019d30bb`, re-backfill via
  `scripts/backfill_nahw_syntax.py` (53,648 head verses, 20,182 `-1`, 3,599
  elided `0`; every `head_index >= 1` resolves inside its own head verse).
  Two follow-up corrections came out of review against the raw corpus:
  * `ref_token_id == 0` is the sentence's **first token**, not a sentinel, so it
    is now resolved like any other reference (+4,982 real edges that were
    previously flattened to `-1`).
  * An elided head is a real corpus edge: 3,599 rows point at a `(*)`
    placeholder (`word_id 0`). They now carry `head_index = 0` instead of being
    reported as sentence roots (word positions are 1-based, so `0` is free).
  The earlier cross-verse fix stands: a head that happens to share the word's
  own position number is a real edge when the head verse differs.
- **`role_key` (extended 2026-10-26)**: exact label first, then the longest
  Arabic marker, so `نائب فاعل` is not swallowed by `فاعل`. The `اسم …` family is
  split into `ism_inna` / `ism_kana` / `ism_kada` / `ism_particle` and `خبر …`
  stays `khabar` (the corpus spelling `لاكن` is treated as `لكن`, and `تكاد` as a
  kada-family verb). Coverage went from 22% to 98.97% of rows (35 keys); 13 rare
  rhetorical labels (801 rows: `مستثني`, `المفعول لأجله`, `اضراب`, …) stay
  `other` because a confident gloss would be a grammar claim, and `role_ar`
  always carries the verbatim label anyway.

## Next actions (in order)

1. Step 7 KMP client wiring for `GET /nahw/verse/...` and `NahwResultScreen`
   (resolve a head as `(head_surah_number, head_ayah_number, head_index)`).
2. Deferred: Redis cache/rate limit, Farasa sidecar, expert-rubric role-accuracy
   evaluation, N6 free-text analysis (plan only, intentionally unbuilt).
