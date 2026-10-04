"""Static catalog of common Classical Arabic noun patterns.

Each entry carries an ``example_lemma`` so the endpoint can attach a real
example word from the ingested corpus at request time. No example strings
are invented per-request; if the lemma is absent from the DB, the endpoint
returns ``example: null``.
"""

from __future__ import annotations

NOUN_PATTERNS: list[dict[str, str]] = [
    {"pattern": "فَعْل", "name": "verbal noun (Form I)", "example_lemma": "حَمْد"},
    {"pattern": "فَعِيل", "name": "intensive/quality adjective", "example_lemma": "رَحِيم"},
    {"pattern": "فُعُول", "name": "plural verbal noun / source", "example_lemma": "عُلُوم"},
    {"pattern": "فَاعِل", "name": "active participle", "example_lemma": "كَاتِب"},
    {"pattern": "مَفْعُول", "name": "passive participle", "example_lemma": "مَكْتُوب"},
    {"pattern": "مَفْعَل", "name": "place/time noun", "example_lemma": "مَسْجِد"},
    {"pattern": "فِعَال", "name": "plural/verbal noun", "example_lemma": "كِتَاب"},
    {"pattern": "فَعَّال", "name": "intensive agent", "example_lemma": "غَفَّار"},
]
