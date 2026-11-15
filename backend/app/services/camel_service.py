from __future__ import annotations

import sqlite3
from collections import OrderedDict
from pathlib import Path
from typing import Any

from app.core.logging import get_logger

logger = get_logger("services.camel")

# CAMeL emits these root values when it has no real root: "O" is the BERT
# disambiguator's OOV fallback (pos noun_prop, lex = surface form) and "NTWS"
# appears on abbreviation entries. Neither is a root.
BAD_ROOT_MARKERS = {"O", "NTWS"}

_LRU_MAX = 256
_cache: OrderedDict[tuple[str, bool], dict[str, Any]] = OrderedDict()
_analyzer: Any = None
_checked_availability = False
_available = False
_bert_disambig: Any = None
_bert_checked = False
_bert_cache: OrderedDict[str, dict[str, Any] | None] = OrderedDict()


def camel_available() -> bool:
    """True if camel-tools is installed in this environment."""
    global _checked_availability, _available
    if _checked_availability:
        return _available
    _checked_availability = True
    try:
        import camel_tools.morphology.analyzer  # noqa: F401
        import camel_tools.morphology.database  # noqa: F401

        _available = True
    except Exception:
        _available = False
    return _available


def _get_analyzer() -> Any:
    """Lazily constructed singleton Analyzer."""
    global _analyzer
    if _analyzer is None:
        from camel_tools.morphology.analyzer import Analyzer
        from camel_tools.morphology.database import MorphologyDB

        _analyzer = Analyzer(MorphologyDB.builtin_db())
        logger.info("CAMeL Analyzer initialized")
    return _analyzer


def _has_real_root(analysis: dict[str, Any]) -> bool:
    root = analysis.get("root")
    if not isinstance(root, str) or not root:
        return False
    cleaned = root.replace(".", "")
    return cleaned not in BAD_ROOT_MARKERS


def convert_weak_placeholders(root: str | None, lex: str | None = None) -> str | None:
    """Resolve CAMeL's ``#`` radical placeholders to concrete letters where possible.

    Inspected in this repo's installed camel_tools (builtin DB, 2026-10-20):
    قول -> ق.#.ل (lex قَوْل, pattern 1َوْ3), خير -> خ.#.ر (1َيْ3),
    ليل -> ل.#.ل (1َيْ3), وجد -> #.ج.د (وَ2َ3), قال -> ق.#.ل (1ا3),
    رمى -> ر.م.# (1َ2َى), دعا -> د.ع.# (1َ2ا), مات -> م.#.ت (1ا3),
    وفى -> #.ف.# (وَ2َى). Doubled radicals are written out in full
    (حلل -> ح.ل.ل, مدد -> م.د.د), so ``#`` is specifically a *weak* radical
    that CAMeL leaves unspecified — the actual weak letter is carried by the
    analysis lemma.

    Resolution: the lemma (diacritics stripped, letters normalised) is
    aligned left-to-right against the strong (non-``#``) radicals; a run of
    consecutive ``#`` slots is filled when the lemma letters in the adjacent
    gap number exactly as many as the run. If alignment fails or gaps do not
    line up, ``#`` is kept — the caller must then treat it as a wildcard over
    weak letters (``morphology_service.score_root_prediction``).

    Accepts dotted (ق.#.ل) and dot-removed (ق#ل) roots and returns the same
    format. Returns ``root`` unchanged when there is nothing to resolve.
    """
    if not root:
        return root
    dotted = "." in root
    slots = root.split(".") if dotted else list(root)
    if "#" not in slots or not lex:
        return root
    from app.services.morphology_service import normalize_arabic

    lex_letters = list(normalize_arabic(lex))
    strong = [i for i, slot in enumerate(slots) if slot != "#"]
    if not strong:
        return root
    positions: list[int] = []
    cursor = 0
    for i in strong:
        letter = normalize_arabic(slots[i])
        try:
            found = lex_letters.index(letter, cursor)
        except ValueError:
            return root
        positions.append(found)
        cursor = found + 1
    resolved = list(slots)

    def fill(run_start: int, run_end: int, gap_start: int, gap_end: int) -> None:
        run_len = run_end - run_start
        if run_len > 0 and gap_end - gap_start == run_len:
            for k in range(run_len):
                resolved[run_start + k] = lex_letters[gap_start + k]

    fill(0, strong[0], 0, positions[0])
    for prev, nxt, prev_pos, next_pos in zip(strong, strong[1:], positions, positions[1:], strict=False):
        fill(prev + 1, nxt, prev_pos + 1, next_pos)
    fill(strong[-1] + 1, len(slots), positions[-1] + 1, len(lex_letters))
    return ".".join(resolved) if dotted else "".join(resolved)


def _spelling_variants(word: str) -> list[str]:
    """Orthographic retries for Quranic imlaei spellings CAMeL's DB misses.

    The corpus stores EQTB-imlaei forms that are often not dictionary words
    (hamza written bare, definite article glued on, ellipsis of doubled or
    missing letters). When the exact form has no usable analysis, retry with
    light spellings: leading hamza seat removed, definite article stripped,
    prefixed conjunction/particle stripped, hamza-seat/ta-marbuta endings.
    Order is preserved and the input word itself is excluded — variants are
    only consulted after the exact form already failed. Only applies to words
    CAMeL does not know at all, so a variant hit cannot displace a correct
    exact analysis.
    """
    variants: list[str] = []

    def add(candidate: str) -> None:
        if candidate and candidate not in variants and candidate != word:
            variants.append(candidate)

    if word[:1] in ("ء", "أ", "إ", "آ"):
        add(word.lstrip("ءأإآ"))
    if word.startswith("ال"):
        add(word[2:])
    if word.startswith("لل"):
        add(word[1:])
        add(word[2:])
    for prefix in ("و", "ف", "ك", "ب", "ل"):
        if word.startswith(prefix):
            rest = word[1:]
            add(rest)
            if rest.startswith("ال"):
                add(rest[2:])
    swapped = word.replace("ؤ", "و").replace("ئ", "ي")
    add(swapped)
    add(swapped.replace("ى", "ي"))
    add(word.replace("ى", "ي"))
    if word.endswith("ة"):
        add(word[:-1] + "ه")
        add(word[:-1])
    if word.endswith("ت") and len(word) > 3:
        add(word[:-1] + "ة")
    return variants


TRAIN_SURAH_SQL = "s.number % 2 = 1"
EVAL_SURAH_SQL = "s.number % 2 = 0"
_LEXICON_DB_PATH = Path(__file__).resolve().parents[2] / "jawhar.db"
_Lexicon = tuple[frozenset[str], frozenset[str], dict[str, str]]
_lexicon: _Lexicon | None = None
_lexicon_exclusion: tuple[int, int] | None = None


def lexicon_key(value: str) -> str:
    """Key used for lemma/root set membership.

    Undiacritised (dagger alif expanded to alef), hamza seats unified
    (ءامن == آمن == امن) and dots stripped, so EQTB gold values and CAMeL
    ``lex``/``root`` values compare. ``ءا`` collapses first because the
    imlaei corpus writes آ that way. Set membership only — never output.
    """
    from app.services.morphology_service import normalize_arabic

    expanded = value.replace("ٰ", "ا")
    return (
        normalize_arabic(expanded)
        .replace("ءا", "ا")
        .replace("ء", "ا")
        .replace("ؤ", "و")
        .replace("ئ", "ي")
        .replace(".", "")
    )


def _exclude_clause(exclude: tuple[int, int] | None) -> str:
    """SQL fragment removing a held-out surah number range (inclusive)."""
    if exclude is None:
        return ""
    low, high = int(exclude[0]), int(exclude[1])
    return f" AND s.number NOT BETWEEN {low} AND {high}"


def _load_lexicon(db_path: Path, exclude: tuple[int, int] | None = None) -> _Lexicon:
    """Build (lemma keys, root keys, lemma->root map) from train (odd) surahs.

    The evaluation samples test (even) surahs (``EVAL_SURAH_SQL``), so no
    eval word's gold label can enter these sets — the ranking signals stay
    non-circular. Placeholder roots and empty values are excluded.
    The lemma->root map holds, per ``lexicon_key(lemma)``, the most frequent
    corpus root (raw ``words.root`` format, e.g. ``قول``; ties broken by
    first occurrence in table order) and feeds ``remap_root_by_lemma``.
    With ``exclude=(low, high)`` the inclusive surah range is removed from
    all three (held-out evaluation): its words appear neither in the
    membership sets nor in the map.
    """
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    excl = _exclude_clause(exclude)
    try:
        lemmas = frozenset(
            lexicon_key(row[0])
            for row in conn.execute(
                "SELECT DISTINCT w.lemma FROM words w"
                " JOIN verses v ON w.verse_id = v.id"
                " JOIN surahs s ON v.surah_id = s.id"
                f" WHERE {TRAIN_SURAH_SQL} AND w.lemma IS NOT NULL AND w.lemma != ''{excl}"
            )
        )
        roots = frozenset(
            lexicon_key(row[0])
            for row in conn.execute(
                "SELECT DISTINCT w.root FROM words w"
                " JOIN verses v ON w.verse_id = v.id"
                " JOIN surahs s ON v.surah_id = s.id"
                f" WHERE {TRAIN_SURAH_SQL} AND w.root IS NOT NULL"
                f" AND w.root != '' AND w.root != 'ـ'{excl}"
            )
        )
        counts: dict[str, dict[str, int]] = {}
        for lemma, root in conn.execute(
            "SELECT w.lemma, w.root FROM words w"
            " JOIN verses v ON w.verse_id = v.id"
            " JOIN surahs s ON v.surah_id = s.id"
            f" WHERE {TRAIN_SURAH_SQL} AND w.lemma IS NOT NULL AND w.lemma != ''"
            f" AND w.root IS NOT NULL AND w.root != '' AND w.root != 'ـ'{excl}"
        ):
            per_lemma = counts.setdefault(lexicon_key(lemma), {})
            per_lemma[root] = per_lemma.get(root, 0) + 1
        lemma_roots = {
            key: max(per_lemma.items(), key=lambda kv: kv[1])[0]
            for key, per_lemma in counts.items()
        }
    finally:
        conn.close()
    return lemmas, roots, lemma_roots


def set_lexicon_exclusion(surah_range: tuple[int, int] | None) -> None:
    """Exclude an inclusive surah number range from the train lexicon.

    Held-out evaluation uses this so the sampled surahs' words appear
    neither in the ranking sets nor in the lemma->root map. Resets the
    process-wide cache; the next ``_get_lexicon`` call reloads.
    """
    global _lexicon_exclusion, _lexicon
    _lexicon_exclusion = surah_range
    _lexicon = None


def _get_lexicon() -> _Lexicon:
    """Process-wide cached train lexicon; empty values when the DB is absent."""
    global _lexicon
    if _lexicon is None:
        try:
            _lexicon = _load_lexicon(_LEXICON_DB_PATH, exclude=_lexicon_exclusion)
        except Exception as exc:
            logger.warning(
                "lexicon load failed (%s); ranking uses analyzer scores only", exc
            )
            _lexicon = (frozenset(), frozenset(), {})
    return _lexicon


def remap_root_by_lemma(analysis: dict[str, Any] | None) -> dict[str, Any] | None:
    """Replace a real CAMeL root with the train-split gold root of its lemma.

    CAMeL spells weak radicals in dictionary form (قال, كان) where the EQTB
    corpus stores the consonantal radical (قول, كون); the corpus records one
    canonical root per lemma, so analyses that carry a real root and a lemma
    attested in the train split (``_load_lexicon``'s lemma->root map) get
    that corpus root instead. Only analyses that already carry a real root
    are touched — placeholder roots and rootless answers stay as they are —
    and only when the lemma is attested with a real root. Returns the input
    object unchanged when nothing applies, else a shallow copy with ``root``
    replaced (corpus format, e.g. ``قول``), so identity comparison tells
    the caller whether a remap happened. Corpus-assisted prediction, not
    analyzer output: callers must attribute it separately.
    """
    if analysis is None or not _has_real_root(analysis):
        return analysis
    lemma = analysis.get("lex")
    if not lemma or not isinstance(lemma, str):
        return analysis
    mapped = _get_lexicon()[2].get(lexicon_key(lemma))
    if not mapped or mapped == analysis.get("root"):
        return analysis
    remapped = dict(analysis)
    remapped["root"] = mapped
    return remapped


def _analysis_score(analysis: dict[str, Any]) -> float:
    """The analyzer's own score: first defined log-prob field, higher is better.

    CAMeL's builtin DB defines pos_lex_logprob/lex_logprob/pos_logprob;
    -99.0 is its "undefined for this entry" sentinel, skipped here. Returns
    -inf when every field is undefined (plain ties in the ranking).
    """
    for field in ("pos_lex_logprob", "lex_logprob", "pos_logprob"):
        value = analysis.get(field)
        if isinstance(value, int | float) and value != -99.0:
            return float(value)
    return float("-inf")


def best_analysis(
    analyses: list[dict[str, Any]],
    lemmas: frozenset[str] | None = None,
    roots: frozenset[str] | None = None,
    *,
    rank: bool = True,
) -> dict[str, Any] | None:
    """Pick the best usable analysis (one with a real root) from ``analyses``.

    Ranking signals, in order:
    1. lemma key attested in ``lemmas`` (train-split gold lemmas),
    2. root key attested in ``roots`` (train-split gold roots),
    3. the analyzer's own score (``_analysis_score``),
    4. original order (``max`` keeps the first on ties).

    With ``rank=False`` the first usable analysis is returned — the old
    behaviour, kept for comparison. Returns None when nothing is usable.
    """
    usable = [a for a in analyses if _has_real_root(a)]
    if not usable:
        return None
    if not rank:
        return usable[0]
    lemma_set = lemmas or frozenset()
    root_set = roots or frozenset()

    def rank_key(analysis: dict[str, Any]) -> tuple[int, int, float]:
        return (
            1 if lexicon_key(str(analysis.get("lex") or "")) in lemma_set else 0,
            1 if lexicon_key(str(analysis.get("root") or "")) in root_set else 0,
            _analysis_score(analysis),
        )

    return max(usable, key=rank_key)


def analyze_with_camel(word: str, *, rank: bool = True) -> dict[str, Any] | None:
    """Run CAMeL on a word; returns the best *usable* analysis dict or None.

    Usable means the analysis carries a real root; OOV/abbreviation
    placeholders ("O", "NTWS") are skipped so callers never see them as
    roots. ``rank=True`` (default) picks with ``best_analysis`` — train-lexicon
    signals, then the analyzer's own score; ``rank=False`` keeps the old
    first-usable behaviour. If the exact spelling yields nothing,
    `_spelling_variants` retries follow. Results are memoized in a small
    in-process LRU cache keyed by (word, rank).
    """
    if not camel_available():
        return None
    cache_key = (word, rank)
    cached = _cache.get(cache_key)
    if cached is not None:
        _cache.move_to_end(cache_key)
        return cached
    try:
        analyzer = _get_analyzer()
        lemmas: frozenset[str] | None = None
        roots: frozenset[str] | None = None
        if rank:
            lemmas, roots, _lemma_roots = _get_lexicon()
        result = best_analysis(analyzer.analyze(word), lemmas, roots, rank=rank)
        if result is None:
            for variant in _spelling_variants(word):
                result = best_analysis(analyzer.analyze(variant), lemmas, roots, rank=rank)
                if result is not None:
                    break
    except Exception as exc:  # data dir missing, etc.
        logger.warning("CAMeL analysis failed for %r: %s", word, exc)
        return None
    if result is not None:
        _cache[cache_key] = result
        _cache.move_to_end(cache_key)
        while len(_cache) > _LRU_MAX:
            _cache.popitem(last=False)
    return result


def bert_available() -> bool:
    global _bert_checked
    if _bert_checked:
        return _bert_disambig is not None
    _bert_checked = True
    try:
        from camel_tools.disambig.bert import BERTUnfactoredDisambiguator  # noqa: F401

        _get_bert_disambig()
        return True
    except Exception:
        return False


def _get_bert_disambig() -> Any:
    global _bert_disambig
    if _bert_disambig is None:
        from camel_tools.disambig.bert import BERTUnfactoredDisambiguator

        _bert_disambig = BERTUnfactoredDisambiguator.pretrained(use_gpu=False)
        logger.info("CAMeL BERT disambiguator initialized")
    return _bert_disambig


def analyze_with_bert(word: str, *, rank: bool = True) -> dict[str, Any] | None:
    """BERT-disambiguated analysis for a single-token sentence (CPU)."""
    if not bert_available():
        return None
    if word in _bert_cache:
        _bert_cache.move_to_end(word)
        return _bert_cache[word]
    try:
        result = _get_bert_disambig().disambiguate([word])
        scored = result[0].analyses
        raw = scored[0].analysis if scored else None
    except Exception as exc:
        logger.warning("BERT disambiguation failed for %r: %s", word, exc)
        return None
    if raw is None or not _has_real_root(raw):
        # BERT's OOV fallback (root "O"/"NTWS", lex = surface form) or no
        # analysis at all: retry the plain analyzer before giving up.
        raw = analyze_with_camel(word, rank=rank) or raw
    _bert_cache[word] = raw
    _bert_cache.move_to_end(word)
    while len(_bert_cache) > _LRU_MAX:
        _bert_cache.popitem(last=False)
    return raw


def disambiguate_verse_with_bert(verse_text: str) -> dict[int, dict[str, Any] | None] | None:
    """BERT-disambiguate every token of a verse in a single model call.

    ``verse_text`` is the verse's stored text (e.g. ``verses.text_imlaei``);
    it is split on whitespace and the whole token sequence is disambiguated
    once, so each word is analysed with its real context instead of as a
    one-token sentence. Returns a dict keyed by 1-based token position
    (matching ``words.position`` whenever the token count equals the verse's
    stored word count) whose values are BERT's chosen analysis dicts, or None
    at positions where the model returned no analyses. Returns None when BERT
    is unavailable, the text is empty, or disambiguation fails. The returned
    analyses are not filtered — placeholder roots come through as-is and
    callers decide the fallback, exactly like the single-word path. Callers
    should compare the key range against the verse's stored word count and
    fall back to ``analyze_with_bert`` per word when they disagree.
    """
    if not bert_available():
        return None
    tokens = verse_text.split()
    if not tokens:
        return None
    try:
        disambiguated = _get_bert_disambig().disambiguate(tokens)
    except Exception as exc:
        logger.warning("BERT verse disambiguation failed: %s", exc)
        return None
    return {
        position: (word.analyses[0].analysis if word.analyses else None)
        for position, word in enumerate(disambiguated, start=1)
    }


def map_camel_output(raw: dict[str, Any], word: str) -> dict[str, Any]:
    """Map CAMeL's analysis dict onto our morphology response shape."""
    root_raw = raw.get("root")
    root = root_raw.replace(".", "") if isinstance(root_raw, str) and root_raw else None
    return {
        "word": word,
        "root": root,
        "lemma": raw.get("lex") or None,
        "pos_tag": raw.get("pos") or None,
        "pattern": raw.get("pattern"),
        "features_json": dict(raw),
    }
