from __future__ import annotations

import pytest

from app.services.nahw_service import ROLE_DEFINITIONS, ROLE_EXACT, role_info


def test_original_legend_entries_keep_their_keys():
    assert role_info("فاعل") == ("subject", "Subject")
    assert role_info("مفعول به") == ("object", "Object")
    assert role_info("مبتدأ") == ("mubtada", "Mubtada")
    assert role_info("خبر") == ("khabar", "Khabar")
    assert role_info("نعت") == ("adjective", "Adjective")
    assert role_info("حرف جر") == ("preposition", "Preposition")
    assert role_info("ظرف") == ("adverb", "Adverb")
    assert role_info("حال") == ("circumstantial", "Circumstantial")


def test_frequent_treebank_labels_get_their_own_keys():
    assert role_info("root")[0] == "root"
    assert role_info("مجرور")[0] == "genitive"
    assert role_info("متعلق")[0] == "attachment"
    assert role_info("معطوف")[0] == "conjoined"
    assert role_info("مضاف إليه")[0] == "mudaf_ilayhi"
    assert role_info("صلة")[0] == "relative_clause"
    assert role_info("صفة")[0] == "adjective"
    assert role_info("بدل")[0] == "appositive"
    assert role_info("توكيد")[0] == "emphasis"
    assert role_info("تمييز")[0] == "specifier"
    assert role_info("منادى")[0] == "vocative"


def test_compound_labels_prefer_the_longest_marker():
    assert role_info("نائب فاعل")[0] == "naib_fail"
    assert role_info("مفعول مطلق")[0] == "absolute_object"
    assert role_info("مفعول به")[0] == "object"
    assert role_info("جواب الشرط")[0] == "condition_answer"
    assert role_info("شرط")[0] == "condition"


def test_khabar_of_a_kawadikh_particle_stays_khabar():
    assert role_info("خبر إن")[0] == "khabar"
    assert role_info("خبر كان")[0] == "khabar"
    assert role_info("خبر عسى")[0] == "khabar"


def test_ism_of_inna_and_kana_families_are_distinguished():
    assert role_info("اسم إن")[0] == "ism_inna"
    assert role_info("اسم كأن")[0] == "ism_inna"
    assert role_info("اسم ليت")[0] == "ism_inna"
    assert role_info("اسم لكن")[0] == "ism_inna"
    assert role_info("اسم لاكن")[0] == "ism_inna"
    assert role_info("اسم كان")[0] == "ism_kana"
    assert role_info("اسم تكون")[0] == "ism_kana"
    assert role_info("اسم ليس")[0] == "ism_kana"
    assert role_info("اسم عسى")[0] == "ism_kada"
    assert role_info("اسم يكاد")[0] == "ism_kada"
    assert role_info("اسم تكاد")[0] == "ism_kada"


def test_unrecognised_ism_family_falls_back_to_a_generic_label():
    assert role_info("اسم لا")[0] == "ism_particle"
    assert role_info("اسم ما")[0] == "ism_particle"


def test_particle_labels_and_unknown_values():
    assert role_info("استفهام")[0] == "interrogative"
    assert role_info("نفي")[0] == "negation"
    assert role_info("نهي")[0] == "prohibition"
    assert role_info("حصر")[0] == "restriction"
    assert role_info("NonRel")[0] == "non_relation"
    assert role_info("something else") == ("other", "Other")
    assert role_info(None) == ("other", "Other")
    assert role_info("   ") == ("other", "Other")


def test_answer_labels_are_not_mistaken_for_condition_or_imperative():
    assert role_info("جواب الشرط")[0] == "condition_answer"
    assert role_info("جواب أمر")[0] == "imperative_answer"
    assert role_info("جواب")[0] == "answer"
    assert role_info("أمر")[0] == "imperative"


def test_every_legend_marker_is_reachable_by_an_exact_label():
    for marker, key, gloss in ROLE_DEFINITIONS:
        assert role_info(marker) == (key, gloss)
    for label, expected in ROLE_EXACT.items():
        assert role_info(label) == expected


@pytest.mark.parametrize(
    "key",
    [key for _, key, _ in ROLE_DEFINITIONS]
    + [key for key, _ in ROLE_EXACT.values()]
    + ["ism_inna", "ism_kana", "ism_kada", "ism_particle"],
)
def test_legend_keys_are_lowercase_snake_case(key: str):
    assert key == key.lower()
    assert " " not in key and "-" not in key
