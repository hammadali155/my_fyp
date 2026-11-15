from __future__ import annotations

import re
from typing import NamedTuple

from app.core.logging import get_logger

logger = get_logger("services.nahw_mapping")


class NahwRole(NamedTuple):
    role_ar: str
    role_key: str
    role_en: str


_OTHER = NahwRole("غير محدد", "other", "Other")

# EQTB-style dependency labels (our `dep_type`/`rel_label` column) mapped to the
# canonical Nahw roles in docs/specs/UI-UX-Design.md section 2.2, broadly following
# the TRD 7.2 guidance (SUBJ->فاعل, OBJ->مفعول به, copulars->مبتدأ/خبر,
# modifiers->نعت, circumstantial->حال).
_DEP_TO_ROLE: dict[str, NahwRole] = {
    "subj": NahwRole("فاعل", "subject", "Subject"),
    "subjac": NahwRole("فاعل", "subject", "Subject"),
    "obj": NahwRole("مفعول به", "object", "Object"),
    "mobtadA": NahwRole("مبتدأ", "mubtada", "Mubtada"),
    "mubtada": NahwRole("مبتدأ", "mubtada", "Mubtada"),
    "pred": NahwRole("خبر", "khabar", "Khabar"),
    "khabar": NahwRole("خبر", "khabar", "Khabar"),
    "adj": NahwRole("نعت", "adjective", "Adjective"),
    "nmod": NahwRole("نعت", "adjective", "Adjective"),
    "circ": NahwRole("حال", "circumstantial", "Circumstantial"),
    "hal": NahwRole("حال", "circumstantial", "Circumstantial"),
    "jard": NahwRole("حرف جر", "preposition", "Preposition"),
    "preposition": NahwRole("حرف جر", "preposition", "Preposition"),
    "zarf": NahwRole("ظرف", "adverb", "Adverb"),
}

_NORMALIZE_RE = re.compile(r"[\s_\-]+")
_logged_unknown: set[str] = set()


def normalize_dep_label(label: str) -> str:
    """Lowercase and strip spaces/underscores/dashes; drop trailing <<in>> style suffixes."""
    cleaned = _NORMALIZE_RE.sub("", label.strip().lower())
    cleaned = re.sub(r"<+[^<>]*>+", "", cleaned)
    return cleaned


def dep_label_to_role(label: str | None) -> NahwRole:
    """Map a dependency label (EQTB/Farasa style) to a canonical Nahw role.

    Unknown or empty labels return the 'other' role and are logged once.
    """
    if not label or not label.strip():
        return _OTHER
    key = normalize_dep_label(label)
    role = _DEP_TO_ROLE.get(key)
    if role is not None:
        return role
    # Prefix-based fallbacks for compound labels, e.g. "subj <<an>>", "pred <<kan>>"
    for prefix, role in (
        ("subj", _DEP_TO_ROLE["subj"]),
        ("pred", _DEP_TO_ROLE["pred"]),
        ("obj", _DEP_TO_ROLE["obj"]),
        ("adj", _DEP_TO_ROLE["adj"]),
        ("circ", _DEP_TO_ROLE["circ"]),
    ):
        if key.startswith(prefix):
            return role
    if key not in _logged_unknown:
        _logged_unknown.add(key)
        logger.warning("Unknown dependency label %r mapped to 'other'", label)
    return _OTHER
