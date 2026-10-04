from __future__ import annotations

from collections import OrderedDict
from typing import Any

from app.core.logging import get_logger

logger = get_logger("services.camel")

_LRU_MAX = 256
_cache: OrderedDict[str, dict[str, Any]] = OrderedDict()
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


def analyze_with_camel(word: str) -> dict[str, Any] | None:
    """Run CAMeL on a word; returns the first analysis dict or None.

    Results are memoized in a small in-process LRU cache.
    """
    if not camel_available():
        return None
    cached = _cache.get(word)
    if cached is not None:
        _cache.move_to_end(word)
        return cached
    try:
        analyses = _get_analyzer().analyze(word)
    except Exception as exc:  # data dir missing, etc.
        logger.warning("CAMeL analysis failed for %r: %s", word, exc)
        return None
    result = analyses[0] if analyses else None
    if result is not None:
        _cache[word] = result
        _cache.move_to_end(word)
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


def analyze_with_bert(word: str) -> dict[str, Any] | None:
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
    _bert_cache[word] = raw
    _bert_cache.move_to_end(word)
    while len(_bert_cache) > _LRU_MAX:
        _bert_cache.popitem(last=False)
    return raw


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
