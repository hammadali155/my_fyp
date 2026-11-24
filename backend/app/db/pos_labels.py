from __future__ import annotations

POS_LABELS: dict[str, str] = {
    "N": "Noun",
    "PN": "Proper noun",
    "ADJ": "Adjective",
    "IMPN": "Imperative verbal noun",
    "PRON": "Personal pronoun",
    "DEM": "Demonstrative pronoun",
    "REL": "Relative pronoun",
    "T": "Time adverb",
    "LOC": "Location adverb",
    "V": "Verb",
    "P": "Preposition",
    "EMPH": "Emphatic lām prefix",
    "IMPV": "Imperative lām prefix",
    "PRP": "Purpose lām prefix",
    "CONJ": "Coordinating conjunction",
    "SUB": "Subordinating conjunction",
    "ACC": "Accusative particle",
    "AMD": "Amendment particle",
    "ANS": "Answer particle",
    "AVR": "Aversion particle",
    "CAUS": "Particle of cause",
    "CERT": "Particle of certainty",
    "CIRC": "Circumstantial particle",
    "COM": "Comitative particle",
    "COND": "Conditional particle",
    "EQ": "Equalization particle",
    "EXH": "Exhortation particle",
    "EXL": "Explanation particle",
    "EXP": "Exceptive particle",
    "FUT": "Future particle",
    "INC": "Inceptive particle",
    "INT": "Particle of interpretation",
    "INTG": "Interrogative particle",
    "NEG": "Negative particle",
    "PREV": "Preventive particle",
    "PRO": "Prohibition particle",
    "REM": "Resumption particle",
    "RES": "Restriction particle",
    "RET": "Retraction particle",
    "RSLT": "Result particle",
    "SUP": "Supplemental particle",
    "SUR": "Surprise particle",
    "VOC": "Vocative particle",
    "INL": "Quranic initials",
}

POS_ORDER: tuple[str, ...] = tuple(POS_LABELS)


def pos_label(code: str | None) -> str | None:
    if code is None:
        return None
    return POS_LABELS.get(code)
