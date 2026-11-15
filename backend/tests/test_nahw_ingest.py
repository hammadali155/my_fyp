from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest
from sqlalchemy import func, select

from app.models.quran import NahwAnnotation, Word
from app.services.nahw_backfill import derive_word_annotations

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def _sample_rows() -> list[dict[str, str]]:
    return [
        {
            "tid": "0", "sentence_id": "1", "sentence_word": "0", "token_id": "0",
            "location": "_", "chapter_id": "1", "verse_id": "1", "word_id": "0",
            "tok_id": "1", "uthmani_token": "(*)", "uthmani_unicode": "(*)",
            "imlaai_token": "(*)", "imlaai_unicode": "(*)", "phonetic": "_",
            "trans": "_", "pos": "V", "pos_ar": "فعل", "features": "_",
            "segment": "STEM", "lemma": "_", "lemma_ar": "ـ", "root": "_",
            "root_ar": "ـ", "verb_form": "_", "prefix": "_", "suffix": "_",
            "verb_aspect": "_", "nominal_state": "_", "verb_mood": "_",
            "special_group": "_", "nominal_case": "_", "derived_nouns": "_",
            "verb_voice": "_", "person": "_", "gender": "_", "number": "_",
            "rel_label": "root", "rel_label_ar": "root", "ref_token_id": "0",
            "is_constituent": "-1", "constituents_loc": "_", "constituents": "_",
            "constituent_label": "-",
        },
        {
            "tid": "1", "sentence_id": "1", "sentence_word": "1", "token_id": "1",
            "location": "(1:1:1:1)", "chapter_id": "1", "verse_id": "1", "word_id": "1",
            "tok_id": "1", "uthmani_token": "بِ", "uthmani_unicode": "bi",
            "imlaai_token": "ب", "imlaai_unicode": "b", "phonetic": "_",
            "trans": "_", "pos": "P", "pos_ar": "حرف جر", "features": "PREFIX|bi+",
            "segment": "PREFIX", "lemma": "_", "lemma_ar": "ـ", "root": "_",
            "root_ar": "ـ", "verb_form": "_", "prefix": "bi+", "suffix": "_",
            "verb_aspect": "_", "nominal_state": "_", "verb_mood": "_",
            "special_group": "_", "nominal_case": "_", "derived_nouns": "_",
            "verb_voice": "_", "person": "_", "gender": "_", "number": "_",
            "rel_label": "link", "rel_label_ar": "متعلق", "ref_token_id": "0",
            "is_constituent": "1", "constituents_loc": "[1-2]", "constituents": "بِسْمِ",
            "constituent_label": "PP",
        },
        {
            "tid": "2", "sentence_id": "1", "sentence_word": "1", "token_id": "2",
            "location": "(1:1:1:2)", "chapter_id": "1", "verse_id": "1", "word_id": "1",
            "tok_id": "2", "uthmani_token": "سْمِ", "uthmani_unicode": "somi",
            "imlaai_token": "سْم", "imlaai_unicode": "som", "phonetic": "bis'mi",
            "trans": "In (the) name", "pos": "N", "pos_ar": "اسم",
            "features": "STEM|POS:N|LEM:{som|ROOT:smw|M|GEN", "segment": "STEM",
            "lemma": "{som", "lemma_ar": "ٱسْم", "root": "smw", "root_ar": "سمو",
            "verb_form": "_", "prefix": "_", "suffix": "_", "verb_aspect": "_",
            "nominal_state": "_", "verb_mood": "_", "special_group": "_",
            "nominal_case": "GEN", "derived_nouns": "_", "verb_voice": "_",
            "person": "_", "gender": "M", "number": "_", "rel_label": "gen",
            "rel_label_ar": "مجرور", "ref_token_id": "1", "is_constituent": "0",
            "constituents_loc": "_", "constituents": "_", "constituent_label": "-",
        },
    ]


def _write_treebank(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-16", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def test_derive_word_annotations_from_three_line_sample():
    derived = derive_word_annotations(_sample_rows())
    assert len(derived) == 1
    annotation = derived[0]
    assert annotation.surah == 1
    assert annotation.ayah == 1
    assert annotation.position == 1
    assert annotation.role == "مجرور"
    assert annotation.dep_type == "gen"
    assert annotation.head_index == -1
    assert annotation.head_surah is None
    assert annotation.head_ayah is None
    assert annotation.irab == "مجرور"
    assert annotation.sentence_index == 1


@pytest.mark.asyncio
async def test_ingest_nahw_stores_the_verse_a_cross_verse_head_lives_in(
    tmp_path, db_session, seed_quran_data
):
    from scripts.ingest_nahw import ingest_nahw

    dependent = _sample_rows()[2] | {
        "tid": "3",
        "sentence_id": "5",
        "token_id": "10",
        "ref_token_id": "20",
        "nominal_case": "GEN",
        "uthmani_token": "ZZ1",
        "imlaai_token": "zz1",
    }
    head = _sample_rows()[2] | {
        "tid": "4",
        "sentence_id": "5",
        "verse_id": "2",
        "token_id": "20",
        "ref_token_id": "0",
        "rel_label": "root",
        "rel_label_ar": "root",
        "uthmani_token": "ZZ2",
        "imlaai_token": "zz2",
    }
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    _write_treebank(corpus_dir / "Quranic.csv", [dependent, head])

    counts, unmapped = await ingest_nahw(db_session, corpus_dir)

    assert counts["rows_inserted"] == 2
    assert unmapped == []
    annotation = (
        await db_session.execute(
            select(NahwAnnotation).where(NahwAnnotation.verse_id == 1)
        )
    ).scalar_one()
    assert annotation.head_index == 1
    assert annotation.head_surah_number == 1
    assert annotation.head_ayah_number == 2
    own_root = (
        await db_session.execute(
            select(NahwAnnotation).where(NahwAnnotation.verse_id == 2)
        )
    ).scalar_one()
    assert own_root.head_index == -1
    assert own_root.head_surah_number is None
    assert own_root.head_ayah_number is None


def test_parse_eqtb_emits_the_head_verse_for_a_cross_verse_head(tmp_path):
    from scripts.ingest_quran import parse_eqtb

    dependent = _sample_rows()[2] | {
        "tid": "3",
        "sentence_id": "5",
        "token_id": "10",
        "ref_token_id": "20",
        "uthmani_token": "ZZ1",
        "imlaai_token": "zz1",
    }
    head = _sample_rows()[2] | {
        "tid": "4",
        "sentence_id": "5",
        "verse_id": "2",
        "token_id": "20",
        "ref_token_id": "0",
        "rel_label": "root",
        "rel_label_ar": "root",
        "uthmani_token": "ZZ2",
        "imlaai_token": "zz2",
    }
    path = tmp_path / "Quranic.csv"
    _write_treebank(path, [dependent, head])

    _, nahw_rows = parse_eqtb(path)

    by_key = {(r["surah"], r["ayah"], r["token_index"]): r for r in nahw_rows}
    dependent_row = by_key[("1", "1", "1")]
    assert dependent_row["head_index"] == "1"
    assert dependent_row["head_surah"] == "1"
    assert dependent_row["head_ayah"] == "2"
    root_row = by_key[("1", "2", "1")]
    assert root_row["head_index"] == "-1"
    assert root_row["head_surah"] == ""
    assert root_row["head_ayah"] == ""


@pytest.mark.asyncio
async def test_ingest_nahw_maps_treebank_to_words_and_is_idempotent(
    tmp_path, db_session, seed_quran_data
):
    from scripts.ingest_nahw import ingest_nahw

    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    _write_treebank(corpus_dir / "Quranic.csv", _sample_rows())

    counts, unmapped = await ingest_nahw(db_session, corpus_dir)

    assert counts["rows_read"] == 3
    assert counts["rows_inserted"] == 1
    assert counts["rows_skipped_total"] == 0
    assert counts["unmapped_tokens"] == 0
    assert unmapped == []

    word_id = (
        await db_session.execute(
            select(Word.id).where(Word.verse_id == 1, Word.position == 1)
        )
    ).scalar_one()
    annotation = (
        await db_session.execute(
            select(NahwAnnotation).where(NahwAnnotation.verse_id == 1)
        )
    ).scalar_one()
    assert annotation.word_id == word_id
    assert annotation.token_index == 1
    assert annotation.role == "مجرور"
    assert annotation.dep_type == "gen"
    assert annotation.head_index == -1
    assert annotation.irab == "مجرور"
    assert annotation.sentence_index == 1

    second_counts, second_unmapped = await ingest_nahw(db_session, corpus_dir)

    assert second_counts["rows_inserted"] == 0
    assert second_counts["rows_skipped_duplicate"] == 1
    assert second_unmapped == []
    total = (
        await db_session.execute(select(func.count()).select_from(NahwAnnotation))
    ).scalar_one()
    assert total == 1


@pytest.mark.asyncio
async def test_ingest_nahw_reports_unmapped_word_without_dropping_it(
    tmp_path, db_session, seed_quran_data
):
    from scripts.ingest_nahw import ingest_nahw

    row = _sample_rows()[2] | {
        "tid": "5",
        "sentence_word": "5",
        "token_id": "5",
        "word_id": "5",
        "ref_token_id": "0",
        "nominal_case": "NOM",
        "rel_label": "subj",
        "rel_label_ar": "فاعل",
    }
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    _write_treebank(corpus_dir / "Quranic.csv", [row])

    counts, unmapped = await ingest_nahw(db_session, corpus_dir)

    assert counts["rows_inserted"] == 0
    assert counts["rows_skipped_word_missing"] == 1
    assert counts["unmapped_tokens"] == 1
    assert unmapped[0]["surah"] == 1
    assert unmapped[0]["ayah"] == 1
    assert unmapped[0]["word_position"] == 5
    assert "word not found" in unmapped[0]["reason"]


@pytest.mark.asyncio
async def test_ingest_nahw_fails_early_when_treebank_is_missing(
    tmp_path, db_session, seed_quran_data
):
    from scripts.ingest_nahw import ingest_nahw

    with pytest.raises(SystemExit, match="Treebank file not found"):
        await ingest_nahw(db_session, tmp_path)
