# Sarf root-extraction baseline — 2026-10-20

Commit: `b2d29ec`. Every run: `--analyzer-only --sample 1000`, corpus never consulted; seeds 42, 7, 123, first plain (mode line: `analyzer-only (CAMeL first analysis)`), then `--bert` (mode line: `analyzer-only (CAMeL BERT disambiguator)`).

Full raw outputs (plain text, stdout + stderr):

- `evaluate_sarf-2026-10-20-b2d29ec-plain-seed42.txt`
- `evaluate_sarf-2026-10-20-b2d29ec-plain-seed7.txt`
- `evaluate_sarf-2026-10-20-b2d29ec-plain-seed123.txt`
- `evaluate_sarf-2026-10-20-b2d29ec-bert-seed42.txt`
- `evaluate_sarf-2026-10-20-b2d29ec-bert-seed7.txt`
- `evaluate_sarf-2026-10-20-b2d29ec-bert-seed123.txt`

## Overall accuracy

Numbers are stated exactly as the script printed them.

| Config | Seed | Rooted words in sample | Rootless words in sample | (a) rooted accuracy | (b) rootless accuracy | (c) combined | Wildcard-dependent matches |
|---|---|---|---|---|---|---|---|
| plain | 42 | 642 | 358 | `452/642 = 0.704` (PRD target 0.90) → BELOW TARGET | `9/358 = 0.025` | `461/1000 = 0.461` | 34 |
| plain | 7 | 647 | 353 | `478/647 = 0.739` (PRD target 0.90) → BELOW TARGET | `2/353 = 0.006` | `480/1000 = 0.480` | 41 |
| plain | 123 | 636 | 364 | `443/636 = 0.697` (PRD target 0.90) → BELOW TARGET | `10/364 = 0.027` | `453/1000 = 0.453` | 30 |
| `--bert` | 42 | 642 | 358 | `484/642 = 0.754` (PRD target 0.90) → BELOW TARGET | `0/358 = 0.000` | `484/1000 = 0.484` | 38 |
| `--bert` | 7 | 647 | 353 | `503/647 = 0.777` (PRD target 0.90) → BELOW TARGET | `0/353 = 0.000` | `503/1000 = 0.503` | 45 |
| `--bert` | 123 | 636 | 364 | `460/636 = 0.723` (PRD target 0.90) → BELOW TARGET | `0/364 = 0.000` | `460/1000 = 0.460` | 34 |

The sample for a given seed is identical across the two configurations (same pool, same seed), so the rooted/rootless split matches between plain and `--bert`.

## Per-POS accuracy (rooted words)

Values are `correct/total = accuracy` exactly as printed; `—` means the POS did not appear in that sample. Totals per column sum to that sample's rooted-word count.

| POS | plain 42 | plain 7 | plain 123 | `--bert` 42 | `--bert` 7 | `--bert` 123 |
|---|---|---|---|---|---|---|
| N | `243/315 = 0.771` | `252/331 = 0.761` | `226/302 = 0.748` | `262/315 = 0.832` | `270/331 = 0.816` | `235/302 = 0.778` |
| V | `139/243 = 0.572` | `170/247 = 0.688` | `153/261 = 0.586` | `147/243 = 0.605` | `175/247 = 0.709` | `162/261 = 0.621` |
| PN | `43/50 = 0.860` | `33/41 = 0.805` | `29/37 = 0.784` | `44/50 = 0.880` | `34/41 = 0.829` | `29/37 = 0.784` |
| ADJ | `19/24 = 0.792` | `16/20 = 0.800` | `29/29 = 1.000` | `21/24 = 0.875` | `16/20 = 0.800` | `28/29 = 0.966` |
| LOC | `4/5 = 0.800` | `6/6 = 1.000` | `4/4 = 1.000` | `5/5 = 1.000` | `6/6 = 1.000` | `4/4 = 1.000` |
| INTG | `2/2 = 1.000` | `0/1 = 0.000` | — | `2/2 = 1.000` | `1/1 = 1.000` | — |
| T | `1/2 = 0.500` | `1/1 = 1.000` | `2/3 = 0.667` | `2/2 = 1.000` | `1/1 = 1.000` | `2/3 = 0.667` |
| COND | `1/1 = 1.000` | — | — | `1/1 = 1.000` | — | — |

## What the numbers say

Rooted-word accuracy stays below the 90% PRD target on every seed in both configurations — plain `0.704 / 0.739 / 0.697`, `--bert` `0.754 / 0.777 / 0.723`, every run printing `BELOW TARGET` — so the target is not met on any of the three seeds, let alone all three. Per-POS, nouns (`N`) are the strongest large class (`0.748`–`0.832`) and verbs (`V`) the weakest (`0.572`–`0.709`), while the small classes (ADJ, LOC, INTG, T, COND) sit at or near `1.000` on single- or double-digit counts that are too small to carry weight. On rootless words neither configuration ever abstains meaningfully — plain `0.025 / 0.006 / 0.027` and `--bert` `0.000 / 0.000 / 0.000` correct because only an empty prediction counts — which drags the combined score to `0.453`–`0.503` despite the rooted-word figures.

## First-analysis vs lexicon-ranked — 2026-10-21 (train/test split)

Commit: `b2d29ec`. Compares the old first-usable analysis pick against the new lexicon ranking (`best_analysis` in `camel_service.py`) on the **same paired samples**.

Protocol:

- Lexicon sets are built once and cached: lemma/root keys from **train = odd-numbered surahs** only — `3112 lemma keys, 1317 root keys` as printed by the script.
- The eval pool is **test = even-numbered surahs only** (`--split test`, 41,205 eligible words), so no eval word's gold label can be in the lexicon — the comparison is non-circular. The script now refuses `--split all` while the lexicon is on.
- Old behaviour = `--no-lexicon`; new behaviour = default (ranked). Runs: `--analyzer-only --split test --sample 1000`, seeds 42 and 7. Mode line for both: `analyzer-only (CAMeL plain analyzer)`; the header prints `lexicon ranking: off ...` vs `lexicon ranking: on ...` and the split.
- Full raw outputs:

  - `evaluate_sarf-2026-10-21-b2d29ec-split-test-first-seed42.txt`
  - `evaluate_sarf-2026-10-21-b2d29ec-split-test-first-seed7.txt`
  - `evaluate_sarf-2026-10-21-b2d29ec-split-test-ranked-seed42.txt`
  - `evaluate_sarf-2026-10-21-b2d29ec-split-test-ranked-seed7.txt`

Numbers exactly as printed:

| Behaviour | Seed | Rooted | Rootless | (a) rooted accuracy | (b) rootless accuracy | (c) combined | Wildcard-dependent matches | Error rows |
|---|---|---|---|---|---|---|---|---|
| first (`--no-lexicon`) | 42 | 632 | 368 | `434/632 = 0.687` → BELOW TARGET | `14/368 = 0.038` | `448/1000 = 0.448` | 39 | 552 |
| ranked (default) | 42 | 632 | 368 | `448/632 = 0.709` → BELOW TARGET | `14/368 = 0.038` | `462/1000 = 0.462` | 41 | 538 |
| first (`--no-lexicon`) | 7 | 657 | 343 | `483/657 = 0.735` → BELOW TARGET | `5/343 = 0.015` | `488/1000 = 0.488` | 37 | 512 |
| ranked (default) | 7 | 657 | 343 | `485/657 = 0.738` → BELOW TARGET | `5/343 = 0.015` | `490/1000 = 0.490` | 40 | 510 |

Per-POS (rooted words), exactly as printed:

| POS | first 42 | ranked 42 | first 7 | ranked 7 |
|---|---|---|---|---|
| N | `218/289 = 0.754` | `228/289 = 0.789` | `250/324 = 0.772` | `250/324 = 0.772` |
| V | `149/259 = 0.575` | `151/259 = 0.583` | `158/254 = 0.622` | `162/254 = 0.638` |
| PN | `33/43 = 0.767` | `33/43 = 0.767` | `35/38 = 0.921` | `35/38 = 0.921` |
| ADJ | `24/30 = 0.800` | `26/30 = 0.867` | `31/32 = 0.969` | `31/32 = 0.969` |
| LOC | `6/7 = 0.857` | `6/7 = 0.857` | `4/4 = 1.000` | `4/4 = 1.000` |
| INTG | `2/2 = 1.000` | `2/2 = 1.000` | `1/1 = 1.000` | `1/1 = 1.000` |
| T | `2/2 = 1.000` | `2/2 = 1.000` | `4/4 = 1.000` | `2/4 = 0.500` |

What the comparison says:

- The ranking improves (a) on both seeds: seed 42 `434 → 448` correct (`0.687 → 0.709`, +14 words), seed 7 `483 → 485` (`0.735 → 0.738`, +2 words). Every run still prints `BELOW TARGET` — the 90% PRD target remains unmet.
- (b) is identical within each seed (the same rootless words pick up a root either way); (c) moves with (a): `0.448 → 0.462` (seed 42), `0.488 → 0.490` (seed 7).
- Per-POS, the seed-42 gain comes mostly from nouns (`218 → 228`) plus ADJ (`24 → 26`) and V (`149 → 151`); seed 7 gains are verbs (`158 → 162`) while nouns do not move, and the tiny `T` class regresses `4/4 → 2/4` (4 items — too small to carry weight).
- These numbers are **not comparable** to the 2026-10-20 table above: the pool differs (even-numbered surahs only vs the whole corpus).
- The repo's `sarf_eval_errors.csv` now holds the ranked seed-7 run (510 rows).

## Whole-verse BERT context — 2026-10-21

Commit: `b2d29ec`. The one-token BERT path (`--bert` on the 2026-10-20 runs) analyses each word as a single-token sentence; this change (`disambiguate_verse_with_bert` in `camel_service.py`) disambiguates the verse's whole stored token sequence in one model call and reads each word's answer at its position. Words of verses whose token count disagrees with the stored word count (468/6236 verses, 7.5% — quranic-mark tokens / missing word rows) fall back to the single-word path; fallback counts are printed. Same paired protocol as the section above: `--bert --split test --sample 1000`, lexicon ranking on, seeds 42 and 7.

Raw outputs:

- `evaluate_sarf-2026-10-21-b2d29ec-split-test-bertverse-seed42.txt`
- `evaluate_sarf-2026-10-21-b2d29ec-split-test-bertverse-seed7.txt`

| Seed | (a) rooted accuracy | (b) rootless | (c) combined | Wildcard matches | Verses one-call / fallback | Word fallbacks |
|---|---|---|---|---|---|---|
| 42 | `488/632 = 0.772` → BELOW TARGET | `0/368 = 0.000` | `488/1000 = 0.488` | 59 | 752 / 67 (87 sample words) | 38 |
| 7 | `525/657 = 0.799` → BELOW TARGET | `0/343 = 0.000` | `525/1000 = 0.525` | 56 | 733 / 64 (103 sample words) | 37 |

Whole-verse context beats both the plain analyzer (`0.709`/`0.738`) and the old one-token BERT numbers (`0.754`/`0.777` on the 2026-10-20 whole-corpus pool — directionally useful, not strictly comparable). Every run still prints `BELOW TARGET`.

## Train-split lemma→root remap — 2026-10-21

Commit: `b2d29ec`. Error bucketing of the two bertverse runs showed 193/276 (69.9%) of group-(a) errors were not wrong roots but EQTB-vs-CAMeL weak-spelling convention differences (gold قول/كون/نوس vs CAMeL قال/كان/ناس), dominated by hollow verbs (قول→قال ×49, كون→كان ×27). The fix (`remap_root_by_lemma` in `camel_service.py`): when a CAMeL analysis carries a real root and a lemma attested in the corpus, replace the root with that lemma's most frequent **train-split (odd-surah)** gold root. The lemma→root map is built with the ranking lexicon (`_load_lexicon`, now 2995 entries — 2970 when the held-out range is excluded), so no even-surah eval word's label can enter it. Only analyses with a real root are touched — rootless answers stay rootless. Remapped predictions are counted (`lemma-remap: N of M …`) and the error CSV's `analyzer` column labels them `+lemma-remap`. This is **corpus-assisted prediction, not analyzer output**; the (a) number below is a pipeline metric. Held-out discipline: `--heldout-surahs LOW-HIGH` samples every eligible word of a surah range and excludes that range from the lexicon *and* the map (the script refuses `--heldout-surahs` with `--via-endpoint`, and refuses `--lemma-remap` with `--split all`).

Raw outputs (test split, `--bert --split test --sample 1000 --lemma-remap`):

- `evaluate_sarf-2026-10-21-b2d29ec-split-test-bertverse-remap-seed1.txt`
- `evaluate_sarf-2026-10-21-b2d29ec-split-test-bertverse-remap-seed42.txt`
- `evaluate_sarf-2026-10-21-b2d29ec-split-test-bertverse-remap-seed7.txt`

Raw outputs (held-out surahs 100–114, all 352 eligible words, range excluded from lexicon and map):

- `evaluate_sarf-2026-10-21-b2d29ec-heldout100-114-plain-noremap.txt`
- `evaluate_sarf-2026-10-21-b2d29ec-heldout100-114-plain-remap.txt`
- `evaluate_sarf-2026-10-21-b2d29ec-heldout100-114-bert-noremap.txt`
- `evaluate_sarf-2026-10-21-b2d29ec-heldout100-114-bert-remap.txt`

| Run | (a) rooted accuracy | (b) rootless | (c) combined | Predictions remapped |
|---|---|---|---|---|
| seed 1, bert+remap | `598/634 = 0.943` → PASS | `0/366 = 0.000` | `598/1000 = 0.598` | 664/1000 |
| seed 42, bert+remap | `574/632 = 0.908` → PASS | `0/368 = 0.000` | `574/1000 = 0.574` | 647/1000 |
| seed 7, bert+remap | `598/657 = 0.910` → PASS | `0/343 = 0.000` | `598/1000 = 0.598` | 654/1000 |
| held-out 100–114, plain | `172/232 = 0.741` → BELOW TARGET | `3/120 = 0.025` | `175/352 = 0.497` | — |
| held-out 100–114, plain+remap | `197/232 = 0.849` → BELOW TARGET | `3/120 = 0.025` | `200/352 = 0.568` | 197/352 |
| held-out 100–114, bert | `180/232 = 0.776` → BELOW TARGET | `0/120 = 0.000` | `180/352 = 0.511` | — |
| held-out 100–114, bert+remap | `202/232 = 0.871` → BELOW TARGET | `0/120 = 0.000` | `202/352 = 0.574` | 181/352 |

## Final summary — 2026-10-21

Best measured configuration: `--bert --split test --lemma-remap` (whole-verse BERT context, lexicon-ranked analysis pick, train-split lemma→root remap; corpus-assisted pipeline).

Rooted-word accuracy, exactly as printed:

| Set | (a) rooted accuracy | Verdict |
|---|---|---|
| Test split, seed 1 (1000-word sample) | `598/634 = 0.943` | PASS |
| Test split, seed 42 (1000-word sample) | `574/632 = 0.908` | PASS |
| Test split, seed 7 (1000-word sample) | `598/657 = 0.910` | PASS |
| Held-out surahs 100–114 (every eligible word, 232 rooted) | `202/232 = 0.871` | BELOW TARGET |

**Is the 90% PRD target met?** On the three test-split sample seeds, yes — all print `PASS`. On the held-out surahs, no (`0.871`). The pre-agreed generalisation guard (revert if held-out is >3 points below the sample) triggered: `0.908`/`0.910`/`0.943` minus `0.871` is 3.7–7.2 points below. Decision (2026-10-21, user-approved): keep the fix, documented honestly — the same-set comparison shows the fix genuinely generalises (held-out `0.741 → 0.849` plain, `0.776 → 0.871` bert), and the held-out set is one region of 15 short surahs, not a second sample of the test distribution. The (a) figure is a **corpus-assisted pipeline metric**: ~65% of test-split predictions (and 181/352 held-out) had their root replaced from the train-split corpus map; the analyzer-only number without the remap is `0.772`/`0.799` (bertverse) and `0.776` (held-out bert). (b) rootless accuracy is `0.000` in every BERT run — BERT always returns an analysis, so the pipeline never abstains; only the plain path abstains at all (`0.025` held-out). Combined accuracy never exceeds `0.598`.

Reproduce (from `backend/`):

```
uv run python ../scripts/evaluate_sarf.py --bert --split test --sample 1000 --seed 42 --lemma-remap
uv run python ../scripts/evaluate_sarf.py --bert --heldout-surahs 100-114 --lemma-remap
```

## Gap to target — 2026-10-21

The held-out set (`0.871`) is below the 90% target; error buckets of the best configuration's error CSVs (group-(a) errors only, classified as in the original bucketing — convention = same root skeleton, weak letter spelled differently; sentinel = CAMeL `O`/`NTWS` placeholders; `#` = unresolvable weak-radical placeholder):

| Bucket | seed 1 | seed 42 | seed 7 | three-seed total | held-out |
|---|---|---|---|---|---|
| Weak-spelling convention (gold قول / pred قال) | 10 | 21 | 26 | 57 | 12 |
| Genuinely wrong analysis | 17 | 17 | 14 | 48 | 7 |
| Sentinel `O`/`NTWS` (CAMeL OOV) | 9 | 18 | 19 | 46 | 11 |
| Unresolvable `#` | 0 | 2 | 0 | 2 | 0 |
| Group-(a) errors total | 36 | 58 | 59 | 153 | 30 |

The convention bucket shrank from 193/276 (69.9%) to 57/153 (37.3%) but was not eliminated — the remap only fires when the analysis lemma is attested in the train split. No claim is made here about any further fix; nothing beyond these measurements has been tested.
