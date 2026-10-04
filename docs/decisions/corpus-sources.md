# Decision Memo: Quran Corpus Data Sources

**Status:** Research complete. Files to be placed in `data/corpus/`. Date: 2026-10-04.

## 1. Tanzil — verse text & translations

- **Source:** https://tanzil.net/docs/download (mirror: King Fahd / qul.tarteel.ai).
- **Format:** "simple text" download, UTF-8, one verse per line:
  `surah|ayah|text` (e.g. `1|1|بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ`).
  XML and SQL variants also offered.
- **Size:** each translation/text file ≈ 0.5–1 MB; 6,236 lines per file.
- **License/attribution:** CC BY 3.0; keep "Tanzil Project" attribution in NOTICE when redistributing. Saheeh International translation: "no rights reserved" per Tanzil. Urdu translations (e.g. Fateh Muhammad Jalandhry, Mahmood-ul-Hasan): distributed via Tanzil, but **verify the specific translator's terms before shipping**.
- **Mapping:** line key `(surah, ayah)` → `verses.text_uthmani` / `text_imlaei` / `translation_en` / `translation_ur`. Text stored byte-for-byte; no normalization.
- **Files to download manually into `data/corpus/`:**
  - `quran-uthmani.txt` (Uthmani script, CC BY 3.0)
  - `quran-imlaei.txt` (simple/imlaei script)
  - `translation-en.txt` (Sahih International)
  - `translation-ur.txt` (Urdu, pick one translator)
- **Count check:** exactly 114 surahs / 6,236 verses — consistent with our targets.

## 2. corpus.quran.com — word-level morphology

- **Source:** https://corpus.quran.com/download → `quranic-corpus-morphology-0.4.txt`.
- **Format:** space-separated, header `LOCATION FORM TAG FEATURES`, one row per
  *morphological segment* (~130,000 segments, 77,430 orthographic words).
  - `LOCATION`: `(surah:ayah:word:segment)` — 4-part numeric ref.
  - `FORM`: segment surface form in **Buckwalter transliteration** (not Arabic script!).
  - `TAG`: coarse tag (e.g. `N`, `V`, `ADJ`, `P`, `PN`).
  - `FEATURES`: pipe/space-joined attributes, e.g. `STEM|POS:N|LEM:{som|ROOT:smw|M|GEN`
    (lemma, root, gender, case, verb form, tense(PF/IMPF/IMPV), person/number …).
- **Size:** ~15 MB.
- **License/attribution:** GPL-licensed annotation (© Kais Dukes 2009–2017); must credit
  corpus.quran.com and link to it. **GPL is a redistribution concern — treat as a dev-time
  reference dataset; do not bundle the file in the app binary/store without legal review.**
- **Mapping to `words` (our row = one orthographic word):**
  - Group rows by `(surah, ayah, word)` (first three parts of LOCATION).
  - `words.text_uthmani` comes from **Tanzil**, not from FORM (FORM is Buckwalter).
  - Top-level `root`, `lemma`, `pos_tag`, `pattern` (e.g. `(IV)`), `tense` (PF/IMPF/IMPV → past/present/imperative), `voice` (ACT/PASS), `gender`, `number`, `person` extracted from the STEM segment's FEATURES.
  - Per-segment rows preserved verbatim in `words.features_json["segments"]`.
- **Count check:** ~128k segment rows but 77,430 unique `(surah,ayah,word)` — consistent
  with our word count target if we group by orthographic word.

## 3. Extended Quranic Treebank (EQTB) — syntax / nahw

- **Source:** Mendeley Data, DOI 10.17632/rk96pn66m4.1 (paper: PMC12361616).
- **Format:** adapted CoNLL-X, TSV, one token per line, 43 columns: 21 morphology columns
  (incl. word position, Uthmani/Imlaai form, POS, lemma, root, prefix/stem/suffix split,
  form/pattern, aspect, mood, voice, person, case, gender, number) + 7 syntactic columns
  (dependency relations, 140 labels using traditional iʿrāb terms).
- **Size:** ~140,000 tokens, tens of MB.
- **License/attribution:** CC BY 4.0 (Mendeley Data, no registration). Cite the EQTB paper.
- **Mapping to `nahw_annotations`:** one EQTB token → one `nahw_annotations` row keyed by
  `(verse_id, token_index)`; `role` ← syntactic relation label (classical term), `dep_type` ← raw label, `head_index` ← head token id, `irab` ← case feature (رفع/نصب/جر/جزم). Link `word_id` via `(verse, token_index)` ↔ `(verse_id, position)`.
- **Count check:** ⚠ EQTB reports **77,439 words** and ~140,000 tokens vs our target of
  77,430 words; base text in EQTB states it was aligned to Tanzil/QADB with morpheme
  boundaries reconciled — expect a small (<100) join-key mismatch to investigate, not to
  paper over. EQTB also covers the full 6,236 verses / 114 surahs.

## Files to download manually (into `data/corpus/`)

| File | Source | Goes to |
|------|--------|---------|
| `quran-uthmani.txt` | Tanzil (simple text) | `verses.text_uthmani` |
| `quran-imlaei.txt` | Tanzil (simple text) | `verses.text_imlaei` |
| `translation-en.txt` | Tanzil (Sahih International) | `verses.translation_en` |
| `translation-ur.txt` | Tanzil (Urdu translator TBD) | `verses.translation_ur` |
| `quranic-corpus-morphology-0.4.txt` | corpus.quran.com/download | `words` morphology via (s,a,w) grouping |
| EQTB data file (CoNLL-X) | Mendeley Data rk96pn66m4.1 | `nahw_annotations` |

## Parser note for `scripts/ingest_quran.py`

The script currently expects `morphology.tsv`/`nahw.tsv` with simple headers. Two options:
(a) adapt its parsers to the real formats above (recommended), or (b) write a one-time
converter producing the TSVs. Decide before ingesting. Also note `morphology` FORM is
Buckwalter transliteration — Arabic script must come from Tanzil, joined on (surah, ayah, word).

## Flags / open conflicts

1. EQTB word count 77,439 vs target 77,430 — investigate join-key mismatches during ingestion. **Resolved:** EQTB yields 77,429 word groups after excluding 4,538 sentence-level `(*)` rows (`word_id=0`); both sources agree on 77,429. The "77,430" doc figure counts one placeholder unit.
2. corpus.quran.com morphology is GPL — do not redistribute without legal review.
3. Urdu translation license must be checked per translator.
4. Tanzil attribution (CC BY 3.0) must be kept in NOTICE/README.

## Ingestion result (2026-10-04)

`scripts/ingest_quran.py` loaded the full corpus into `backend/jawhar.db` in ~3m43s:
114 surahs, 6,236 verses, 77,429 words, 77,429 nahw_annotations, 0 verse-level word-count
differences vs EQTB. Update the "6,236 verses, 77,430 words" references in PRD/TRD/AGENTS.md
to 77,429 when next editing those docs.
