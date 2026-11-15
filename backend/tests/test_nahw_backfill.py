from __future__ import annotations

import csv
from contextlib import asynccontextmanager

import pytest
from sqlalchemy import select

from app.models.quran import NahwAnnotation
from app.services.nahw_backfill import (
    QURANIC_IRAB,
    derive_word_annotations,
    quranic_irab,
)


def _row(
    *,
    chapter: str,
    verse: str,
    word: str,
    tok: str,
    token_id: str,
    segment: str = "STEM",
    sentence: str = "1",
    rel_label: str = "Subj",
    rel_label_ar: str = "فاعل",
    ref_token_id: str = "0",
    nominal_case: str = "_",
    verb_mood: str = "_",
    uthmani_token: str = "",
) -> dict[str, str]:
    return {
        "chapter_id": chapter,
        "verse_id": verse,
        "word_id": word,
        "tok_id": tok,
        "token_id": token_id,
        "segment": segment,
        "sentence_id": sentence,
        "rel_label": rel_label,
        "rel_label_ar": rel_label_ar,
        "ref_token_id": ref_token_id,
        "nominal_case": nominal_case,
        "verb_mood": verb_mood,
        "uthmani_token": uthmani_token,
    }


# Real rows from Quranic.csv for 1:1 (sentence 1). Tokens:
#   token 0 word 0 STEM root (بسم placeholder)  -> not a real word
#   token 1 word 1 PREFIX link  ref 0
#   token 2 word 1 STEM   gen   ref 1  -> head token 1 = word 1 (own word, prefix)
#   token 3 word 2 STEM   Poss  ref 2  -> head token 2 = word 1  (cross-word)
#   token 4 word 3 PREFIX NonRel ref 4
#   token 5 word 3 STEM   Adj   ref 3  -> head token 3 = word 2  (cross-word)
#   token 6 word 4 PREFIX NonRel ref 6
#   token 7 word 4 STEM   Adj   ref 3  -> head token 3 = word 2  (cross-word)
def _fatiha_1_1() -> list[dict[str, str]]:
    return [
        _row(chapter="1", verse="1", word="0", tok="1", token_id="0", segment="STEM", rel_label="root", rel_label_ar="root", ref_token_id="0"),
        _row(chapter="1", verse="1", word="1", tok="1", token_id="1", segment="PREFIX", rel_label="link", rel_label_ar="متعلق", ref_token_id="0"),
        _row(chapter="1", verse="1", word="1", tok="2", token_id="2", rel_label="gen", rel_label_ar="مجرور", ref_token_id="1", nominal_case="GEN"),
        _row(chapter="1", verse="1", word="2", tok="1", token_id="3", rel_label="Poss", rel_label_ar="مضاف إليه", ref_token_id="2", nominal_case="GEN"),
        _row(chapter="1", verse="1", word="3", tok="1", token_id="4", segment="PREFIX", rel_label="NonRel", rel_label_ar="NonRel", ref_token_id="4"),
        _row(chapter="1", verse="1", word="3", tok="2", token_id="5", rel_label="Adj", rel_label_ar="صفة", ref_token_id="3", nominal_case="GEN"),
        _row(chapter="1", verse="1", word="4", tok="1", token_id="6", segment="PREFIX", rel_label="NonRel", rel_label_ar="NonRel", ref_token_id="6"),
        _row(chapter="1", verse="1", word="4", tok="2", token_id="7", rel_label="Adj", rel_label_ar="صفة", ref_token_id="3", nominal_case="GEN"),
    ]


def test_derive_head_index_from_sentence_scoped_tokens():
    anns = derive_word_annotations(_fatiha_1_1())

    by_pos = {a.position: a for a in anns}
    assert sorted(by_pos) == [1, 2, 3, 4]

    # word 1 STEM head token 1 -> its own word's prefix -> word-level: sentence root (-1)
    assert by_pos[1].head_index == -1
    assert by_pos[1].head_surah is None
    assert by_pos[1].head_ayah is None
    # word 2 STEM head token 2 -> word 1 (same verse)
    assert by_pos[2].head_index == 1
    assert (by_pos[2].head_surah, by_pos[2].head_ayah) == (1, 1)
    # words 3 and 4 head token 3 -> word 2 (same verse)
    assert by_pos[3].head_index == 2
    assert by_pos[4].head_index == 2
    assert (by_pos[3].head_surah, by_pos[3].head_ayah) == (1, 1)
    assert (by_pos[4].head_surah, by_pos[4].head_ayah) == (1, 1)

    assert by_pos[1].role == "مجرور"
    assert by_pos[1].dep_type == "gen"
    assert by_pos[3].role == "صفة"


def test_sentence_index_is_recorded():
    anns = derive_word_annotations(_fatiha_1_1())
    assert {a.sentence_index for a in anns} == {1}


def test_sentence_spanning_two_verses_shares_token_scope():
    # 1:2 and 1:3 are one sentence in EQTB (sentence 2); token ids are scoped by
    # (chapter, sentence), so a 1:3 word may point at a 1:2 token.
    rows = [
        _row(chapter="1", verse="2", word="1", tok="2", token_id="1", rel_label="root", rel_label_ar="root", ref_token_id="0", uthmani_token="حَمْدُ", sentence="2"),
        _row(chapter="1", verse="2", word="2", tok="1", token_id="3", segment="PREFIX", rel_label="link", rel_label_ar="متعلق", ref_token_id="1", sentence="2"),
        _row(chapter="1", verse="2", word="2", tok="2", token_id="4", rel_label="gen", rel_label_ar="مجرور", ref_token_id="3", sentence="2"),
        _row(chapter="1", verse="3", word="1", tok="2", token_id="9", rel_label="Adj", rel_label_ar="صفة", ref_token_id="4", sentence="2"),
    ]
    # 1:3 word 1 head token 4 resolves, within sentence 2, to 1:2 word 2.
    anns = derive_word_annotations(rows)
    verse_1_3 = [a for a in anns if a.surah == 1 and a.ayah == 3][0]
    assert verse_1_3.head_index == 2
    assert verse_1_3.head_surah == 1
    assert verse_1_3.head_ayah == 2
    assert verse_1_3.sentence_index == 2


def test_cross_verse_head_that_shares_the_words_own_position_is_not_own_prefix():
    # The head sits at word position 1 but lives in 1:2, so it is a real edge to
    # another verse — not the word's own prefix.
    rows = [
        _row(chapter="1", verse="2", word="1", tok="2", token_id="1", rel_label="root", rel_label_ar="root", ref_token_id="0", sentence="2"),
        _row(chapter="1", verse="3", word="1", tok="2", token_id="9", rel_label="Adj", rel_label_ar="صفة", ref_token_id="1", sentence="2"),
    ]
    anns = derive_word_annotations(rows)
    verse_1_3 = [a for a in anns if a.ayah == 3][0]
    assert verse_1_3.head_index == 1
    assert (verse_1_3.head_surah, verse_1_3.head_ayah) == (1, 2)


def test_elided_head_uses_the_zero_sentinel():
    rows = [
        _row(chapter="1", verse="2", word="1", tok="2", token_id="1", rel_label="root", rel_label_ar="root", ref_token_id="0"),
        _row(chapter="1", verse="2", word="0", tok="1", token_id="2", rel_label="Pred", rel_label_ar="خبر", ref_token_id="1"),
        _row(chapter="1", verse="2", word="2", tok="3", token_id="3", rel_label="Pred", rel_label_ar="خبر", ref_token_id="2"),
    ]
    anns = derive_word_annotations(rows)
    # word 2 points at token 2 which is the elided placeholder (word_id 0) -> 0
    by_pos = {a.position: a for a in anns}
    assert by_pos[2].head_index == 0
    assert by_pos[2].head_surah is None
    assert by_pos[2].head_ayah is None


def test_ref_token_id_zero_resolves_to_the_sentences_first_token():
    # ref_token_id 0 means "the sentence's first token", not a sentinel: 2:2
    # كِتَٰبُ (بدل) really points at ذَٰلِكَ.
    rows = [
        _row(chapter="2", verse="2", word="1", tok="1", token_id="0", rel_label="root", rel_label_ar="root", ref_token_id="0"),
        _row(chapter="2", verse="2", word="2", tok="2", token_id="1", rel_label="App", rel_label_ar="بدل", ref_token_id="0"),
    ]
    anns = derive_word_annotations(rows)
    by_pos = {a.position: a for a in anns}
    assert by_pos[1].head_index == -1
    assert by_pos[2].head_index == 1
    assert (by_pos[2].head_surah, by_pos[2].head_ayah) == (2, 2)


def test_clitic_pointing_at_its_own_word_is_not_a_head():
    rows = [
        _row(chapter="2", verse="2", word="1", tok="1", token_id="0", rel_label="root", rel_label_ar="root", ref_token_id="0"),
        _row(chapter="2", verse="2", word="1", tok="2", token_id="1", segment="PREFIX", rel_label="NonRel", rel_label_ar="NonRel", ref_token_id="1"),
        _row(chapter="2", verse="2", word="1", tok="3", token_id="2", rel_label="gen", rel_label_ar="مجرور", ref_token_id="1", nominal_case="GEN"),
    ]
    anns = derive_word_annotations(rows)
    assert anns[0].head_index == -1
    assert anns[0].head_surah is None
    assert anns[0].head_ayah is None


def test_multiple_stems_per_word_uses_first_by_tok_id():
    rows = [
        _row(chapter="2", verse="1", word="1", tok="2", token_id="1", rel_label="root", rel_label_ar="root", ref_token_id="0"),
        _row(chapter="2", verse="1", word="2", tok="1", token_id="2", rel_label="Subj", rel_label_ar="فاعل", ref_token_id="1"),
        _row(chapter="2", verse="1", word="2", tok="3", token_id="3", rel_label="Obj", rel_label_ar="مفعول به", ref_token_id="1"),
    ]
    anns = derive_word_annotations(rows)
    word2 = [a for a in anns if a.position == 2][0]
    # first STEM by tok_id (tok 1) wins, matching the ingest script
    assert word2.dep_type == "Subj"
    assert word2.role == "فاعل"


def test_quranic_irab_translates_case_and_mood():
    assert quranic_irab("NOM", "_") == "مرفوع"
    assert quranic_irab("ACC", "_") == "منصوب"
    assert quranic_irab("GEN", "_") == "مجرور"
    assert quranic_irab("_", "MOOD:SUBJ") == "منصوب"
    assert quranic_irab("_", "MOOD:JUS") == "مجزوم"
    assert quranic_irab("_", "_") is None
    # case wins when both present (nominals never carry a verb mood)
    assert quranic_irab("NOM", "MOOD:SUBJ") == "مرفوع"
    assert set(QURANIC_IRAB.values()) == {"مرفوع", "منصوب", "مجرور", "مجزوم"}


@pytest.mark.asyncio
async def test_backfill_script_writes_derived_values_and_is_rerun_safe(
    tmp_path, db_session, seed_quran_data, monkeypatch
):
    from scripts import backfill_nahw_syntax

    rows = [
        _row(chapter="1", verse="1", word="1", tok="1", token_id="1", rel_label="root", rel_label_ar="root", ref_token_id="1"),
        _row(chapter="1", verse="1", word="2", tok="2", token_id="2", rel_label="gen", rel_label_ar="مجرور", ref_token_id="1", nominal_case="GEN"),
        _row(chapter="1", verse="1", word="3", tok="3", token_id="3", rel_label="Adj", rel_label_ar="صفة", ref_token_id="1", nominal_case="GEN"),
        _row(chapter="1", verse="1", word="4", tok="4", token_id="4", rel_label="Adj", rel_label_ar="صفة", ref_token_id="1", nominal_case="GEN"),
    ]
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    with (corpus_dir / "Quranic.csv").open("w", encoding="utf-16", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)

    for position in range(1, 5):
        db_session.add(
            NahwAnnotation(
                verse_id=1,
                word_id=position,
                token_index=position,
                role="stale",
                dep_type="stale",
                head_index=99,
                head_surah_number=9,
                head_ayah_number=9,
                irab="stale",
                sentence_index=9,
            )
        )
    await db_session.commit()

    @asynccontextmanager
    async def _session_scope():
        yield db_session

    monkeypatch.setattr(backfill_nahw_syntax, "async_session_factory", _session_scope)

    dry = await backfill_nahw_syntax.backfill(corpus_dir=corpus_dir, dry_run=True)
    assert (dry["derived_total"], dry["stored_total"], dry["updated"]) == (4, 4, 4)
    assert dry["unchanged"] == 0
    stored = (
        await db_session.execute(
            select(NahwAnnotation).where(NahwAnnotation.token_index == 1)
        )
    ).scalar_one()
    await db_session.refresh(stored)
    assert stored.head_index == 99  # dry run wrote nothing

    first = await backfill_nahw_syntax.backfill(corpus_dir=corpus_dir, dry_run=False)
    assert first["updated"] == 4
    assert first["unchanged"] == 0

    second = await backfill_nahw_syntax.backfill(corpus_dir=corpus_dir, dry_run=False)
    assert second["updated"] == 0
    assert second["unchanged"] == 4

    rows_by_position = {
        row.token_index: row
        for row in (
            await db_session.execute(
                select(NahwAnnotation).where(NahwAnnotation.verse_id == 1)
            )
        ).scalars()
    }
    assert rows_by_position[1].head_index == -1
    assert rows_by_position[1].head_surah_number is None
    assert rows_by_position[1].irab is None
    assert rows_by_position[2].head_index == 1
    assert (rows_by_position[2].head_surah_number, rows_by_position[2].head_ayah_number) == (1, 1)
    assert rows_by_position[2].irab == "مجرور"
    assert rows_by_position[2].sentence_index == 1
