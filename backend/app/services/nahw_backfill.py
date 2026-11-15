from __future__ import annotations

from dataclasses import dataclass

# EQTB nominal_case / verb_mood values translated to the classical i'rab terms
# used throughout the specs (رفع/نصب/جر/جزم). The mapping is 1:1 and total —
# never a judgement call — and case is only ever read from `nominal_case` while
# mood is only ever read from `verb_mood`, so a noun never gets a mood label.
QURANIC_IRAB: dict[str, str] = {
    "NOM": "مرفوع",
    "ACC": "منصوب",
    "GEN": "مجرور",
    "MOOD:SUBJ": "منصوب",
    "MOOD:JUS": "مجزوم",
}

_NO_HEAD = -1
_ELIDED_HEAD = 0


@dataclass(frozen=True)
class DerivedAnnotation:
    """One derived word-level annotation, keyed by (surah, ayah, position).

    ``head_index`` semantics (word positions are 1-based, so both sentinels are
    outside the valid range):

    * ``-1`` — no separate head word: the EQTB sentence root, a clitic that
      attaches to its own word, or an unresolvable reference.
    * ``0`` — the head is an elided element EQTB records as a placeholder row
      (``word_id == 0``, rendered ``(*)``), e.g. the ``خبر`` of ``لا`` in 2:2.
    * ``>= 1`` — the head's word position inside the verse named by
      ``head_surah``/``head_ayah`` (which may not be the annotated word's verse).
    """

    surah: int
    ayah: int
    position: int
    role: str | None
    dep_type: str | None
    head_index: int
    irab: str | None
    sentence_index: int
    head_surah: int | None = None
    head_ayah: int | None = None


def quranic_irab(nominal_case: str, verb_mood: str) -> str | None:
    """Translate EQTB case/mood to the classical i'rab term (None when absent)."""
    if nominal_case and nominal_case != "_":
        return QURANIC_IRAB.get(nominal_case)
    if verb_mood and verb_mood != "_":
        return QURANIC_IRAB.get(verb_mood)
    return None


def derive_word_annotations(
    rows: list[dict[str, str]],
) -> list[DerivedAnnotation]:
    """Derive word-level annotations from raw EQTB rows.

    ``rows`` are the raw dict rows of ``Quranic.csv`` (one per segment). The
    derivation mirrors the ingest script's word grouping (one row per
    orthographic word, the first ``STEM`` by ``tok_id`` wins) and resolves the
    EQTB head reference (``ref_token_id``) into a word-level ``head_index``.

    Head references are scoped by ``(chapter_id, sentence_id)`` — an EQTB
    sentence can span verse boundaries, so ``token_id`` never keys on the verse.
    ``ref_token_id`` is a token id *inside that sentence* (``0`` is the
    sentence's first token, not a sentinel), so it is resolved like any other
    reference. The resolved token carries the head's word id and its own verse,
    which is what makes a cross-verse head unambiguous: the head's word position
    alone does not say where the head lives. ``head_index`` is that head *word
    position* and ``head_surah``/``head_ayah`` name its verse (both ``None``
    whenever ``head_index <= 0``). See :class:`DerivedAnnotation` for the meaning
    of ``-1`` and ``0``.
    """
    by_word: dict[tuple[int, int, int], list[dict[str, str]]] = {}
    for row in rows:
        if row["word_id"] == "0":
            continue
        key = (int(row["chapter_id"]), int(row["verse_id"]), int(row["word_id"]))
        by_word.setdefault(key, []).append(row)

    scope: dict[tuple[str, str], dict[str, tuple[str, int, int]]] = {}
    for row in rows:
        scope.setdefault((row["chapter_id"], row["sentence_id"]), {})[row["token_id"]] = (
            row["word_id"],
            int(row["chapter_id"]),
            int(row["verse_id"]),
        )

    derived: list[DerivedAnnotation] = []
    for (surah, ayah, position), word_rows in by_word.items():
        ordered = sorted(word_rows, key=lambda r: int(r["tok_id"]))
        stem = next((r for r in ordered if r["segment"] == "STEM"), ordered[0])
        sentence = stem["sentence_id"]
        sentence_index = int(sentence)

        head_index = _NO_HEAD
        head_surah: int | None = None
        head_ayah: int | None = None
        ref = stem["ref_token_id"]
        head = scope.get((stem["chapter_id"], sentence), {}).get(ref) if ref else None
        if head is not None:
            head_word, head_chapter, head_verse = head
            if head_word == "0":
                head_index = _ELIDED_HEAD
            elif not (
                head_word == str(position) and head_chapter == surah and head_verse == ayah
            ):
                head_index = int(head_word)
                head_surah = head_chapter
                head_ayah = head_verse

        derived.append(
            DerivedAnnotation(
                surah=surah,
                ayah=ayah,
                position=position,
                role=stem["rel_label_ar"] or stem["rel_label"],
                dep_type=stem["rel_label"],
                head_index=head_index,
                irab=quranic_irab(stem["nominal_case"], stem["verb_mood"]),
                sentence_index=sentence_index,
                head_surah=head_surah,
                head_ayah=head_ayah,
            )
        )
    return derived
