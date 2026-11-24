from __future__ import annotations

from app.services.lesson_seed import LEVEL_BANDS, lesson_specs, rank_roots


def test_rank_roots_filters_placeholders_and_rare_roots() -> None:
    rows = [("ب", 5), ("ا", 5), ("ج", 2), ("ـ", 9), ("د", 3)]
    ranked = rank_roots(rows, min_occurrences=3)
    assert ranked == [("ا", 5), ("ب", 5), ("د", 3)]


def test_rank_roots_breaks_ties_by_root_string() -> None:
    ranked = rank_roots([("علم", 7), ("رحم", 7), ("قول", 7)], min_occurrences=1)
    assert [root for root, _ in ranked] == ["رحم", "علم", "قول"]


def test_lesson_specs_fill_the_three_bands() -> None:
    ranked = [(f"root{i}", 1000 - i) for i in range(1, 401)]
    specs = lesson_specs(ranked)

    by_level = {level: [s for s in specs if s.level == level] for level in LEVEL_BANDS}
    assert len(by_level["beginner"]) == 40
    assert len(by_level["intermediate"]) == 80
    assert len(by_level["advanced"]) == 180
    assert by_level["beginner"][0].rank == 1
    assert by_level["beginner"][0].sequence == 1
    assert by_level["intermediate"][0].rank == 41
    assert by_level["intermediate"][0].sequence == 1
    assert by_level["advanced"][-1].rank == 300
    assert by_level["advanced"][-1].sequence == 180


def test_lesson_specs_stop_when_roots_run_out() -> None:
    ranked = [(f"root{i}", 500 - i) for i in range(1, 51)]
    specs = lesson_specs(ranked)
    assert len(specs) == 50
    assert sum(1 for s in specs if s.level == "beginner") == 40
    assert sum(1 for s in specs if s.level == "intermediate") == 10
    assert sum(1 for s in specs if s.level == "advanced") == 0
