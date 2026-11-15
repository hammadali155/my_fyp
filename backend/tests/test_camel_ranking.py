from __future__ import annotations

import sqlite3
from collections import OrderedDict
from types import SimpleNamespace

from app.services import camel_service

# Three hand-made analyses of one fake word, designed so the ranking
# signals disagree with the analyzer's own score:
#   A_SCORED: no lexicon-set hit, best analyzer score  (signal 3)
#   A_LEMMA:  lemma attested in the train set          (signal 1)
#   A_BOTH:   lemma and root attested                  (signals 1 + 2)
A_SCORED = {"root": "ز.ي.ت", "lex": "زَيْت", "pos": "noun", "pos_lex_logprob": -1.0}
A_LEMMA = {"root": "ب.ر.ق", "lex": "بَرْق", "pos": "noun", "pos_lex_logprob": -50.0}
A_BOTH = {"root": "ق.ر.أ", "lex": "قَرَأَ", "pos": "verb", "pos_lex_logprob": -99.0}

LEMMAS = frozenset(
    {camel_service.lexicon_key("بَرْق"), camel_service.lexicon_key("قَرَأَ")}
)
ROOTS = frozenset({camel_service.lexicon_key("ق.ر.أ")})


def test_best_analysis_signal_order():
    assert camel_service.best_analysis([A_SCORED, A_LEMMA, A_BOTH], LEMMAS, ROOTS) is A_BOTH
    assert camel_service.best_analysis([A_SCORED, A_LEMMA], LEMMAS, ROOTS) is A_LEMMA
    assert camel_service.best_analysis([A_SCORED, A_BOTH], LEMMAS, ROOTS) is A_BOTH
    assert camel_service.best_analysis([A_LEMMA, A_BOTH], LEMMAS, ROOTS) is A_BOTH


def test_best_analysis_score_fallback_and_original_order():
    low = {"root": "ك.ذ.ب", "lex": "كَذَب", "pos": "verb", "pos_lex_logprob": -99.0}
    high = {"root": "ن.ظ.ر", "lex": "نَظَرَ", "pos": "verb", "lex_logprob": -2.0}
    assert camel_service.best_analysis([low, high]) is high
    assert camel_service.best_analysis([high, low]) is high

    tied_a = {"root": "س.م.ى", "lex": "سَمَا", "pos": "noun"}
    tied_b = {"root": "ر.م.ى", "lex": "رَمَا", "pos": "noun"}
    assert camel_service.best_analysis([tied_a, tied_b]) is tied_a
    assert camel_service.best_analysis([tied_b, tied_a]) is tied_b


def test_best_analysis_skips_placeholders_and_returns_none_when_unusable():
    oov = {"root": "O", "lex": "يوف", "pos": "noun_prop"}
    abbr = {"root": "NTWS", "lex": "ntws", "pos": "noun_abbr"}
    good = {"root": "و.ف.#", "lex": "وَفَى", "pos": "verb"}
    assert camel_service.best_analysis([oov, good]) is good
    assert camel_service.best_analysis([good, oov]) is good
    assert camel_service.best_analysis([oov, abbr]) is None
    assert camel_service.best_analysis([]) is None


def test_best_analysis_rank_false_is_old_first_behaviour():
    assert (
        camel_service.best_analysis(
            [A_SCORED, A_LEMMA, A_BOTH], LEMMAS, ROOTS, rank=False
        )
        is A_SCORED
    )
    oov = {"root": "O", "lex": "يوف", "pos": "noun_prop"}
    assert camel_service.best_analysis([oov, A_SCORED], LEMMAS, ROOTS, rank=False) is A_SCORED


def test_lexicon_key_membership_normalization():
    assert camel_service.lexicon_key("ءَامَن") == camel_service.lexicon_key("امن")
    assert camel_service.lexicon_key("ق.ر.أ") == camel_service.lexicon_key("قرا")
    assert camel_service.lexicon_key("كِتَٰب") == camel_service.lexicon_key("كتاب")
    assert "." not in camel_service.lexicon_key("ق.ر.أ")


def test_analyze_with_camel_ranking_with_fake_analyzer(monkeypatch):
    analyses = [A_SCORED, A_LEMMA, A_BOTH]
    fake_analyzer = SimpleNamespace(analyze=lambda word: analyses)
    monkeypatch.setattr(camel_service, "camel_available", lambda: True)
    monkeypatch.setattr(camel_service, "_get_analyzer", lambda: fake_analyzer)
    monkeypatch.setattr(camel_service, "_cache", OrderedDict())
    monkeypatch.setattr(camel_service, "_get_lexicon", lambda: (LEMMAS, ROOTS, {}))

    assert camel_service.analyze_with_camel("فَعَلَ") is A_BOTH
    assert camel_service.analyze_with_camel("فَعَلَ", rank=False) is A_SCORED

    monkeypatch.setattr(camel_service, "_cache", OrderedDict())
    assert camel_service.analyze_with_camel("فَعَلَ", rank=False) is A_SCORED
    assert camel_service.analyze_with_camel("فَعَلَ") is A_BOTH


def test_load_lexicon_train_split_only(tmp_path):
    db_path = tmp_path / "lexicon.db"
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE surahs (id INTEGER PRIMARY KEY, number INTEGER);
        CREATE TABLE verses (id INTEGER PRIMARY KEY, surah_id INTEGER);
        CREATE TABLE words (
            id INTEGER PRIMARY KEY,
            verse_id INTEGER,
            lemma TEXT,
            root TEXT
        );
        INSERT INTO surahs (id, number) VALUES (1, 1), (2, 2);
        INSERT INTO verses (id, surah_id) VALUES (1, 1), (2, 2);
        INSERT INTO words (id, verse_id, lemma, root) VALUES
            (1, 1, 'كِتَٰب', 'كتب'),
            (2, 1, NULL, 'ـ'),
            (3, 1, '', 'د.ر.س'),
            (4, 2, 'غُرَاب', 'غ.ر.ب');
        """
    )
    conn.commit()
    conn.close()

    lemmas, roots, lemma_roots = camel_service._load_lexicon(db_path)

    assert camel_service.lexicon_key("كِتَٰب") in lemmas
    assert camel_service.lexicon_key("غُرَاب") not in lemmas
    assert "" not in lemmas

    assert camel_service.lexicon_key("كتب") in roots
    assert camel_service.lexicon_key("د.ر.س") in roots
    assert camel_service.lexicon_key("غ.ر.ب") not in roots
    assert camel_service.lexicon_key("ـ") not in roots

    assert lemma_roots == {camel_service.lexicon_key("كِتَٰب"): "كتب"}


def test_load_lexicon_excludes_heldout_range(tmp_path):
    db_path = tmp_path / "lexicon.db"
    conn = sqlite3.connect(db_path)
    conn.executescript(
        """
        CREATE TABLE surahs (id INTEGER PRIMARY KEY, number INTEGER);
        CREATE TABLE verses (id INTEGER PRIMARY KEY, surah_id INTEGER);
        CREATE TABLE words (
            id INTEGER PRIMARY KEY,
            verse_id INTEGER,
            lemma TEXT,
            root TEXT
        );
        INSERT INTO surahs (id, number) VALUES (1, 1), (2, 101), (3, 113), (4, 2);
        INSERT INTO verses (id, surah_id) VALUES (1, 1), (2, 2), (3, 3), (4, 4);
        INSERT INTO words (id, verse_id, lemma, root) VALUES
            (1, 1, 'كِتَٰب', 'كتب'),
            (2, 2, 'نَصَر', 'نصر'),
            (3, 3, 'قَلْب', 'قلب'),
            (4, 4, 'مَلَك', 'ملك');
        """
    )
    conn.commit()
    conn.close()

    unfiltered = camel_service._load_lexicon(db_path)
    assert camel_service.lexicon_key("نَصَر") in unfiltered[0]
    assert unfiltered[2][camel_service.lexicon_key("نَصَر")] == "نصر"

    lemmas, roots, lemma_roots = camel_service._load_lexicon(db_path, exclude=(100, 114))

    assert camel_service.lexicon_key("كِتَٰب") in lemmas
    for key in ("نَصَر", "قَلْب", "مَلَك"):
        assert camel_service.lexicon_key(key) not in lemmas

    assert camel_service.lexicon_key("كتب") in roots
    for key in ("نصر", "قلب", "ملك"):
        assert camel_service.lexicon_key(key) not in roots

    assert set(lemma_roots) == {camel_service.lexicon_key("كِتَٰب")}


def test_remap_root_by_lemma(monkeypatch):
    monkeypatch.setattr(
        camel_service,
        "_get_lexicon",
        lambda: (frozenset(), frozenset(), {camel_service.lexicon_key("قَالَ"): "قول"}),
    )

    hollow = {"root": "ق.ا.ل", "lex": "قَالَ", "pos": "verb"}
    remapped = camel_service.remap_root_by_lemma(hollow)
    assert remapped is not hollow
    assert remapped["root"] == "قول"
    assert remapped["lex"] == "قَالَ"
    assert hollow["root"] == "ق.ا.ل"

    same = {"root": "قول", "lex": "قَالَ", "pos": "verb"}
    assert camel_service.remap_root_by_lemma(same) is same

    unattested = {"root": "ك.ت.ب", "lex": "كَتَبَ", "pos": "verb"}
    assert camel_service.remap_root_by_lemma(unattested) is unattested

    placeholder = {"root": "O", "lex": "قَالَ", "pos": "noun_prop"}
    assert camel_service.remap_root_by_lemma(placeholder) is placeholder

    no_lemma = {"root": "ق.ا.ل"}
    assert camel_service.remap_root_by_lemma(no_lemma) is no_lemma

    assert camel_service.remap_root_by_lemma(None) is None


def test_set_lexicon_exclusion_resets_cache(monkeypatch):
    seen: list[tuple[int, int] | None] = []

    def fake_load(path, exclude=None):
        seen.append(exclude)
        return frozenset(), frozenset(), {}

    monkeypatch.setattr(camel_service, "_load_lexicon", fake_load)
    monkeypatch.setattr(camel_service, "_lexicon", None)
    monkeypatch.setattr(camel_service, "_lexicon_exclusion", None)

    camel_service._get_lexicon()
    assert seen == [None]

    camel_service.set_lexicon_exclusion((100, 114))
    camel_service._get_lexicon()
    camel_service._get_lexicon()
    assert seen == [None, (100, 114)]

    camel_service.set_lexicon_exclusion(None)
    camel_service._get_lexicon()
    assert seen == [None, (100, 114), None]


def test_get_lexicon_cached_and_survives_missing_db(monkeypatch, tmp_path):
    calls: list[int] = []
    triple = (frozenset({"a"}), frozenset({"b"}), {"x": "y"})

    def fake_load(path, exclude=None):
        calls.append(1)
        if path.name == "missing.db":
            raise sqlite3.OperationalError("unable to open database file")
        return triple

    monkeypatch.setattr(camel_service, "_load_lexicon", fake_load)
    monkeypatch.setattr(camel_service, "_lexicon", None)
    assert camel_service._get_lexicon() is triple
    assert camel_service._get_lexicon() is triple
    assert len(calls) == 1

    monkeypatch.setattr(camel_service, "_lexicon", None)
    monkeypatch.setattr(camel_service, "_LEXICON_DB_PATH", tmp_path / "missing.db")
    assert camel_service._get_lexicon() == (frozenset(), frozenset(), {})
