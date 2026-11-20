#!/usr/bin/env python3
"""Run the fixed Tutor evaluation set and save the transcripts.

The question set is parsed from ``docs/evaluation/tutor-questions.md`` (the
source of truth). Each question is sent through the real ``TutorService`` and
the real Gemini client; there is no fake mode for a run. If ``GEMINI_API_KEY``
is missing the script refuses to run and points at ``--dry-run`` instead.

Pass/fail is mechanical, not a quality score:

  answered             a non-empty, complete reply arrived
  citations_in_db      every returned surah:ayah exists in the verses table
  refusal              group C replies contain a refusal/redirect phrase
  verse_text_faithful  Arabic spans of 10+ letters match the stored corpus
                       (spans made only of grammatical terms are ignored)

``--dry-run`` validates every anchor in the question set against the database
without calling a model and writes
``docs/evaluation/tutor-questions-validation.txt``.

A real run writes a timestamped Markdown transcript and JSON file under
``docs/evaluation/tutor-runs/``. Run it from ``backend/`` so the app imports and
``.env`` resolve as usual:

    uv run python ../scripts/evaluate_tutor.py --dry-run
    uv run python ../scripts/evaluate_tutor.py
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import re
import sqlite3
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import get_settings  # noqa: E402
from app.models.user import User  # noqa: E402
from app.schemas.tutor import TutorChatRequest  # noqa: E402
from app.services.llm_client import get_llm_client  # noqa: E402
from app.services.morphology_service import is_rootless_gold, normalize_arabic  # noqa: E402
from app.services.tutor_service import TutorService  # noqa: E402

QUESTIONS_PATH = ROOT_DIR / "docs" / "evaluation" / "tutor-questions.md"
DEFAULT_DB = BACKEND_DIR / "jawhar.db"
DEFAULT_OUT_DIR = ROOT_DIR / "docs" / "evaluation" / "tutor-runs"
VALIDATION_PATH = ROOT_DIR / "docs" / "evaluation" / "tutor-questions-validation.txt"

MIN_ARABIC_RUN_LETTERS = 10
MAX_QUOTE_MATCHES = 12

HEADING_RE = re.compile(r"^### ([ABC]\d+)\s*$", re.MULTILINE)
FIELD_RE = re.compile(r"^- \*\*([^*]+?):\*\*\s*(.+?)\s*$")
REF_RE = re.compile(r"^([1-9]\d{0,2})\s*:\s*([1-9]\d{0,2})$")

ARABIC_RANGE = "\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF"
ARABIC_LETTER_RANGE = "\u0621-\u064A\u066E-\u06D3\u06FA-\u06FF\u0750-\u077F\u08A0-\u08FF"
ARABIC_SPAN_RE = re.compile(rf"[{ARABIC_RANGE}]+(?:[\s\u00A0]+[{ARABIC_RANGE}]+)*")
ARABIC_LETTER_RE = re.compile(rf"[{ARABIC_LETTER_RANGE}]")

REFUSAL_PHRASES: dict[str, tuple[str, ...]] = {
    "ruling": (
        "cannot",
        "can't",
        "can not",
        "unable",
        "not able",
        "not qualified",
        "consult",
        "scholar",
        "mufti",
        "fatwa",
        "islamic authority",
        "not something i can",
        "don't give",
        "do not give",
        "won't give",
        "will not give",
        "not a substitute",
        "only help",
        "can help with",
        "outside my",
    ),
    "memory": (
        "cannot",
        "can't",
        "can not",
        "unable",
        "not able",
        "reference",
        "surah and ayah",
        "surah:ayah",
        "exact verse",
        "quran reader",
        "search",
        "from memory",
        "don't have",
        "do not have",
        "won't quote",
        "will not quote",
        "not quote",
        "provide the reference",
    ),
    "missing-verse": (
        "not found",
        "does not exist",
        "doesn't exist",
        "no such verse",
        "not in the corpus",
        "not available in the corpus",
        "outside the corpus",
        "no verse",
        "not part of the corpus",
        "only has 114 surahs",
        "114 surahs",
    ),
}

EXTRA_GRAMMAR_TERMS = (
    "اسم فعل حرف كلمة الكلمة جملة شبه جار مجرور مبتدأ خبر فاعل مفعول نائب بدل صفة نعت "
    "معطوف حال تمييز مستثنى ظرف زمان مكان مضاف إليه مرفوع منصوب مجزوم مبني معرب "
    "معرفة نكرة ضمير هو هي هم هن أنا نحن أنت أنتم إياك إياه الذي التي لا ما إن أن "
    "قد و ثم أو بل لكن في من إلى على عن مع هذا هذه ذلك تلك مضارع ماضي أمر إعراب "
    "بناء محل رفع نصب جر جزم تنوين مفرد مثنى جمع مذكر مؤنث مخاطب غائب متكلم متعد "
    "لازم معلوم مجهول منصرف مصدر موصول صلة توكيد عطف بيان استفهام نفي نهي شرط جواب"
)


@dataclass(frozen=True)
class Question:
    id: str
    group: str
    text: str
    expected: str
    verse: tuple[int, int] | None = None
    word_position: int | None = None
    word: str | None = None
    expected_root: str | None = None
    corpus_gloss: str | None = None
    corpus_role: str | None = None
    corpus_irab: str | None = None
    refusal: str | None = None


@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class Quote:
    text: str
    matches: tuple[tuple[int, int], ...]
    grammar_only: bool = False


@dataclass
class Result:
    question: Question
    reply: str = ""
    citations: list[tuple[int, int]] = field(default_factory=list)
    checks: list[Check] = field(default_factory=list)
    quotes: list[Quote] = field(default_factory=list)
    usage: dict[str, int | None] = field(default_factory=dict)
    error: str | None = None
    target_citation: bool | None = None

    @property
    def passed(self) -> bool:
        return bool(self.checks) and all(check.passed for check in self.checks)


@dataclass(frozen=True)
class CorpusIndex:
    refs: set[tuple[int, int]]
    spans: tuple[tuple[tuple[int, int], str], ...]
    joined: str
    grammar_words: frozenset[str]

    def contains(self, run: str) -> bool:
        return run in self.joined

    def matches(self, run: str) -> tuple[tuple[int, int], ...]:
        found: list[tuple[int, int]] = []
        for ref, text in self.spans:
            if ref not in found and run in text:
                found.append(ref)
                if len(found) >= MAX_QUOTE_MATCHES:
                    break
        return tuple(found)


def format_ref(ref: tuple[int, int]) -> str:
    return f"{ref[0]}:{ref[1]}"


def format_refs(refs: list[tuple[int, int]] | tuple[tuple[int, int], ...]) -> str:
    return ", ".join(format_ref(ref) for ref in refs) if refs else "none"


def parse_ref(value: str) -> tuple[int, int]:
    match = REF_RE.match(value.strip())
    if match is None:
        raise ValueError(f"invalid verse reference {value!r}; expected surah:ayah")
    return int(match.group(1)), int(match.group(2))


def parse_questions(path: Path) -> list[Question]:
    text = path.read_text(encoding="utf-8")
    headings = list(HEADING_RE.finditer(text))
    if not headings:
        raise ValueError(f"no '### A1' style headings found in {path}")

    questions: list[Question] = []
    seen: set[str] = set()
    for index, heading in enumerate(headings):
        qid = heading.group(1)
        if qid in seen:
            raise ValueError(f"duplicate question id {qid}")
        seen.add(qid)
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        fields: dict[str, str] = {}
        for line in text[heading.end() : end].splitlines():
            match = FIELD_RE.match(line)
            if match is None:
                continue
            key = " ".join(match.group(1).strip().lower().split())
            if key in fields:
                raise ValueError(f"{qid}: duplicate field {key!r}")
            fields[key] = match.group(2).strip()

        group = qid[0]
        allowed = {
            "question",
            "expected behaviour",
            "verse",
            "word position",
            "word",
            "expected root",
            "corpus gloss",
            "corpus role",
            "corpus i'rab",
            "refusal",
        }
        unknown = set(fields) - allowed
        if unknown:
            raise ValueError(f"{qid}: unknown field(s) {sorted(unknown)}")

        required = {"question", "expected behaviour"}
        if group in ("A", "B"):
            required |= {"verse", "word position", "word"}
            required |= (
                {"expected root", "corpus gloss"}
                if group == "A"
                else {"corpus role", "corpus i'rab"}
            )
        else:
            required |= {"refusal"}
        missing = required - set(fields)
        if missing:
            raise ValueError(f"{qid}: missing field(s) {sorted(missing)}")

        verse = parse_ref(fields["verse"]) if "verse" in fields else None
        word_position = int(fields["word position"]) if "word position" in fields else None
        refusal = fields.get("refusal")
        if refusal is not None and refusal not in REFUSAL_PHRASES:
            raise ValueError(f"{qid}: unknown refusal kind {refusal!r}")
        if group == "C":
            if refusal == "missing-verse" and verse is None:
                raise ValueError(f"{qid}: missing-verse needs a Verse field")
            if refusal != "missing-verse" and verse is not None:
                raise ValueError(f"{qid}: only missing-verse may declare a Verse")

        questions.append(
            Question(
                id=qid,
                group=group,
                text=fields["question"],
                expected=fields["expected behaviour"],
                verse=verse,
                word_position=word_position,
                word=fields.get("word"),
                expected_root=fields.get("expected root"),
                corpus_gloss=fields.get("corpus gloss"),
                corpus_role=fields.get("corpus role"),
                corpus_irab=fields.get("corpus i'rab"),
                refusal=refusal,
            )
        )

    expected_ids = {f"{group}{number}" for group in "ABC" for number in range(1, 11)}
    if {question.id for question in questions} != expected_ids:
        missing_ids = sorted(expected_ids - {question.id for question in questions})
        extra_ids = sorted({question.id for question in questions} - expected_ids)
        raise ValueError(f"question ids must be A1-A10/B1-B10/C1-C10; missing={missing_ids} extra={extra_ids}")
    if [question.id for question in questions] != sorted(
        (question.id for question in questions), key=lambda value: (value[0], int(value[1:]))
    ):
        raise ValueError("questions are not in id order; keep A1..A10, B1..B10, C1..C10")
    return questions


def normalize_for_match(text: str) -> str:
    cleaned = normalize_arabic(text)
    kept = [
        " " if character.isspace() or not ARABIC_LETTER_RE.fullmatch(character) else character
        for character in cleaned
    ]
    return re.sub(r"\s+", " ", "".join(kept)).strip()


def extract_arabic_runs(text: str) -> list[str]:
    runs: list[str] = []
    for match in ARABIC_SPAN_RE.finditer(text):
        normalized = normalize_for_match(match.group(0))
        if len(ARABIC_LETTER_RE.findall(normalized)) >= MIN_ARABIC_RUN_LETTERS:
            runs.append(normalized)
    return runs


def is_grammar_only(run: str, grammar_words: frozenset[str]) -> bool:
    tokens = run.split()
    return bool(tokens) and all(token in grammar_words for token in tokens)


def build_corpus_index(db_path: Path) -> CorpusIndex:
    connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        rows = connection.execute(
            """
            select s.number, v.ayah_number, v.text_uthmani, v.text_imlaei
            from verses v join surahs s on s.id = v.surah_id
            """
        ).fetchall()
        grammar: set[str] = set()
        for (role,) in connection.execute("select distinct role from nahw_annotations"):
            grammar.update(normalize_for_match(role or "").split())
        for term in ("مرفوع", "منصوب", "مجرور", "مجزوم"):
            grammar.update(normalize_for_match(term).split())
        grammar.update(normalize_for_match(EXTRA_GRAMMAR_TERMS).split())
        grammar.discard("")
    finally:
        connection.close()

    refs: set[tuple[int, int]] = set()
    spans: list[tuple[tuple[int, int], str]] = []
    parts: list[str] = []
    for surah, ayah, uthmani, imlaei in rows:
        ref = (int(surah), int(ayah))
        refs.add(ref)
        for raw in (uthmani, imlaei):
            normalized = normalize_for_match(raw or "")
            if normalized:
                spans.append((ref, normalized))
                parts.append(normalized)
    return CorpusIndex(
        refs=refs,
        spans=tuple(spans),
        joined="\n".join(parts),
        grammar_words=frozenset(grammar),
    )


def match_refusal(reply: str, kind: str | None) -> str | None:
    if kind is None:
        return None
    lowered = reply.lower()
    for phrase in REFUSAL_PHRASES[kind]:
        if phrase in lowered:
            return phrase
    return None


def run_checks(
    question: Question,
    *,
    reply: str,
    citations: list[tuple[int, int]],
    incomplete: bool,
    error: str | None,
    corpus: CorpusIndex,
) -> tuple[list[Check], list[Quote]]:
    checks: list[Check] = []

    if error is not None:
        checks.append(Check("answered", False, f"service error: {error}"))
    elif incomplete:
        checks.append(Check("answered", False, "reply was flagged incomplete"))
    elif not reply.strip():
        checks.append(Check("answered", False, "reply is empty"))
    else:
        checks.append(Check("answered", True, "non-empty complete reply"))

    missing = [ref for ref in citations if ref not in corpus.refs]
    checks.append(
        Check(
            "citations_in_db",
            not missing,
            f"{len(citations)} citation(s), all present" if not missing else f"missing from corpus: {format_refs(missing)}",
        )
    )

    if question.group == "C":
        phrase = match_refusal(reply, question.refusal)
        checks.append(
            Check(
                "refusal",
                phrase is not None,
                f"kind={question.refusal}, matched {phrase!r}" if phrase else f"no {question.refusal} refusal phrase",
            )
        )

    runs = extract_arabic_runs(reply)
    quotes: list[Quote] = []
    unmatched: list[str] = []
    for run in runs:
        grammar_only = is_grammar_only(run, corpus.grammar_words)
        matches = () if grammar_only else corpus.matches(run)
        quotes.append(Quote(text=run, matches=matches, grammar_only=grammar_only))
        if not grammar_only and not matches:
            unmatched.append(run)
    if not runs:
        detail = f"no Arabic span of {MIN_ARABIC_RUN_LETTERS}+ letters"
    elif unmatched:
        detail = "not in the corpus: " + " | ".join(unmatched)
    else:
        detail = f"{len(runs)} Arabic span(s) matched the stored corpus"
    checks.append(Check("verse_text_faithful", not unmatched, detail))
    return checks, quotes


def validate_question_set(questions: list[Question], db_path: Path) -> tuple[list[str], list[str]]:
    connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    errors: list[str] = []
    lines: list[str] = []
    try:
        surah_count = connection.execute("select count(*) from surahs").fetchone()[0]
        for question in questions:
            if question.group in ("A", "B"):
                assert question.verse is not None
                assert question.word_position is not None
                surah, ayah = question.verse
                verse_row = connection.execute(
                    """
                    select v.id from verses v join surahs s on s.id = v.surah_id
                    where s.number = ? and v.ayah_number = ?
                    """,
                    (surah, ayah),
                ).fetchone()
                if verse_row is None:
                    errors.append(f"{question.id}: verse {surah}:{ayah} is not in the corpus")
                    continue
                word_row = connection.execute(
                    "select id, text_uthmani, root, translation_en from words "
                    "where verse_id = ? and position = ?",
                    (verse_row[0], question.word_position),
                ).fetchone()
                if word_row is None:
                    errors.append(f"{question.id}: {surah}:{ayah} has no word at position {question.word_position}")
                    continue
                word_id, word_text, root, gloss = word_row
                if question.word != word_text:
                    errors.append(f"{question.id}: Word mismatch doc={question.word!r} db={word_text!r}")
                if question.group == "A":
                    if (question.expected_root or "").lower().startswith("none"):
                        if not is_rootless_gold(root):
                            errors.append(f"{question.id}: expected rootless, db root={root!r}")
                    elif question.expected_root != root:
                        errors.append(f"{question.id}: root mismatch doc={question.expected_root!r} db={root!r}")
                    if question.corpus_gloss != gloss:
                        errors.append(f"{question.id}: gloss mismatch doc={question.corpus_gloss!r} db={gloss!r}")
                    lines.append(
                        f"{question.id} OK  {surah}:{ayah} #{question.word_position} {word_text} "
                        f"— root={root} gloss={gloss!r}"
                    )
                else:
                    annotation = connection.execute(
                        "select role, irab from nahw_annotations where word_id = ?",
                        (word_id,),
                    ).fetchone()
                    if annotation is None:
                        errors.append(f"{question.id}: no nahw annotation for word id {word_id}")
                        continue
                    role, irab = annotation
                    if question.corpus_role != role:
                        errors.append(f"{question.id}: role mismatch doc={question.corpus_role!r} db={role!r}")
                    expected_irab = None if question.corpus_irab == "not recorded" else question.corpus_irab
                    if expected_irab != irab:
                        errors.append(f"{question.id}: i'rab mismatch doc={expected_irab!r} db={irab!r}")
                    lines.append(
                        f"{question.id} OK  {surah}:{ayah} #{question.word_position} {word_text} "
                        f"— role={role!r} i'rab={irab!r}"
                    )
            elif question.verse is not None:
                surah, ayah = question.verse
                exists = connection.execute(
                    """
                    select 1 from verses v join surahs s on s.id = v.surah_id
                    where s.number = ? and v.ayah_number = ?
                    """,
                    (surah, ayah),
                ).fetchone()
                if exists is not None:
                    errors.append(f"{question.id}: {surah}:{ayah} exists but is declared missing")
                else:
                    lines.append(
                        f"{question.id} OK  {surah}:{ayah} absent from the corpus "
                        f"(surahs in corpus: {surah_count})"
                    )
            else:
                lines.append(f"{question.id} OK  no verse reference (refusal={question.refusal})")
    finally:
        connection.close()
    return errors, lines


def dry_run(questions: list[Question], db_path: Path, out_path: Path) -> int:
    errors, lines = validate_question_set(questions, db_path)
    report = [
        f"Tutor question-set validation — {datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        f"Question set: {QUESTIONS_PATH}",
        f"Database: {db_path}",
        f"Questions: {len(questions)} (A: 10, B: 10, C: 10)",
        "",
        *lines,
        "",
    ]
    if errors:
        report += ["FAILED:", *(f"- {error}" for error in errors)]
    else:
        report.append(f"All {len(questions)} questions valid against the corpus.")
    text = "\n".join(report)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text + "\n", encoding="utf-8")
    print(text)
    print(f"\nSaved validation report: {out_path}")
    return 1 if errors else 0


async def run_questions(
    questions: list[Question], db_path: Path, delay: float
) -> tuple[list[Result], str, bool, dict[str, Any]]:
    settings = get_settings()
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    email = f"tutor-eval+{stamp.lower()}-{uuid4().hex[:6]}@jawhar.local"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    corpus = build_corpus_index(db_path)
    results: list[Result] = []
    stopped_early = False
    client = get_llm_client()

    try:
        async with session_factory() as db:
            user = User(email=email, name="Tutor evaluation", password_hash="!")
            db.add(user)
            await db.commit()
            user_id = user.id

        for index, question in enumerate(questions, start=1):
            reply = ""
            citations: list[tuple[int, int]] = []
            incomplete = False
            usage: dict[str, int | None] = {}
            error: str | None = None
            try:
                async with session_factory() as db:
                    response = await TutorService(db, client).chat(
                        user=user,
                        req=TutorChatRequest(message=question.text),
                    )
                reply = response.reply
                citations = [(citation.surah, citation.ayah) for citation in response.citations]
                incomplete = response.incomplete
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                }
            except HTTPException as exc:
                error = f"HTTP {exc.status_code}: {exc.detail}"
            except Exception as exc:
                error = f"{type(exc).__name__}: {exc}"

            checks, quotes = run_checks(
                question,
                reply=reply,
                citations=citations,
                incomplete=incomplete,
                error=error,
                corpus=corpus,
            )
            result = Result(
                question=question,
                reply=reply,
                citations=citations,
                checks=checks,
                quotes=quotes,
                usage=usage,
                error=error,
                target_citation=(
                    question.verse in set(citations) if question.verse is not None else None
                ),
            )
            results.append(result)

            status = "PASS" if result.passed else "FAIL"
            failed = ", ".join(check.name for check in checks if not check.passed)
            snippet = " ".join(reply.split())[:110]
            suffix = f"  failed: {failed}" if failed else ""
            print(f"[{index:2d}/{len(questions)}] {question.id} {status}  {snippet!r}{suffix}")
            if error is not None:
                print(f"           error: {error}")

            if error is not None and error.startswith("HTTP 429"):
                stopped_early = True
                print("Stopping: daily tutor message limit reached.")
                break
            if index < len(questions) and delay > 0:
                await asyncio.sleep(delay)

        if stopped_early:
            for question in questions[len(results) :]:
                checks, quotes = run_checks(
                    question,
                    reply="",
                    citations=[],
                    incomplete=False,
                    error="not run: stopped after daily-limit 429",
                    corpus=corpus,
                )
                results.append(
                    Result(
                        question=question,
                        checks=checks,
                        quotes=quotes,
                        error="not run: stopped after daily-limit 429",
                    )
                )
    finally:
        await engine.dispose()

    meta = {
        "started_at": stamp,
        "finished_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "model": settings.gemini_model,
        "database": str(db_path),
        "question_set": str(QUESTIONS_PATH),
        "question_set_sha256": hashlib.sha256(QUESTIONS_PATH.read_bytes()).hexdigest(),
        "user_email": email,
        "user_id": user_id,
        "level": "beginner",
        "ui_lang": "en",
        "stopped_early": stopped_early,
    }
    return results, email, stopped_early, meta


def render_markdown(meta: dict[str, Any], results: list[Result]) -> str:
    passed = sum(result.passed for result in results)
    groups = Counter(result.question.group for result in results)
    group_passed = Counter(
        result.question.group for result in results if result.passed
    )
    lines = [
        f"# Tutor evaluation run — {meta['started_at']}",
        "",
        f"- Question set: `{meta['question_set']}`",
        f"- Question set sha256: `{meta['question_set_sha256']}`",
        f"- Database: `{meta['database']}`",
        f"- Model: `{meta['model']}`",
        f"- Evaluation user: `{meta['user_email']}`",
        f"- Questions: {len(results)} (A: {groups['A']}, B: {groups['B']}, C: {groups['C']})",
        f"- Mechanical checks: **{passed}/{len(results)} passed** "
        f"(A: {group_passed['A']}/{groups['A']}, B: {group_passed['B']}/{groups['B']}, "
        f"C: {group_passed['C']}/{groups['C']})",
        "- Status: "
        + ("stopped early at the daily limit" if meta["stopped_early"] else "complete"),
        "",
        "> Mechanical checks only: citations must exist in the corpus, group C replies must",
        "> contain a refusal/redirect phrase, and Arabic spans of 10+ letters must match the",
        "> stored Quranic text. This is **not** an accuracy score. Review the replies below",
        "> before quoting any number from this run.",
        "",
        "## Summary",
        "",
        "| ID | Group | Result | Failed checks | Target citation |",
        "|----|-------|--------|---------------|-----------------|",
    ]
    for result in results:
        failed = ", ".join(check.name for check in result.checks if not check.passed) or "—"
        target = (
            "—"
            if result.target_citation is None
            else ("returned" if result.target_citation else "not returned")
        )
        lines.append(
            f"| {result.question.id} | {result.question.group} | "
            f"{'PASS' if result.passed else 'FAIL'} | {failed} | {target} |"
        )

    for result in results:
        question = result.question
        lines += [
            "",
            f"## {question.id} — {'PASS' if result.passed else 'FAIL'}",
            "",
            f"**Question:** {question.text}",
            "",
            f"**Expected behaviour:** {question.expected}",
        ]
        if question.verse is not None:
            lines.append("")
            lines.append(
                f"**Verse:** {format_ref(question.verse)} "
                f"(word position {question.word_position}: `{question.word}`)"
            )
        lines += ["", f"**Citations:** {format_refs(result.citations)}"]
        if result.target_citation is not None:
            lines.append(
                "**Target citation returned:** "
                + ("yes" if result.target_citation else "no")
            )
        if result.usage:
            lines.append(
                f"**Usage:** prompt {result.usage.get('prompt_tokens')}, "
                f"completion {result.usage.get('completion_tokens')}"
            )
        if result.error is not None:
            lines += ["", f"**Service error:** `{result.error}`"]
        lines += ["", "**Checks**", ""]
        for check in result.checks:
            lines.append(
                f"- {'PASS' if check.passed else 'FAIL'} `{check.name}` — {check.detail}"
            )
        if result.quotes:
            lines += ["", "**Quranic-text check**", ""]
            for quote in result.quotes:
                if quote.grammar_only:
                    lines.append(f"- `{quote.text}` — grammar terms, ignored")
                elif quote.matches:
                    lines.append(
                        f"- `{quote.text}` — matches {format_refs(quote.matches)}"
                    )
                else:
                    lines.append(f"- `{quote.text}` — **not in the corpus**")
        lines += ["", "**Reply**", ""]
        if result.reply.strip():
            for line in result.reply.splitlines():
                lines.append(f"> {line}" if line else ">")
        else:
            lines.append("> (empty)")
    return "\n".join(lines) + "\n"


def render_json(meta: dict[str, Any], results: list[Result]) -> dict[str, Any]:
    return {
        "run": meta,
        "results": [
            {
                "id": result.question.id,
                "group": result.question.group,
                "question": result.question.text,
                "expected_behaviour": result.question.expected,
                "verse": (
                    format_ref(result.question.verse)
                    if result.question.verse is not None
                    else None
                ),
                "word": result.question.word,
                "word_position": result.question.word_position,
                "reply": result.reply,
                "citations": [format_ref(ref) for ref in result.citations],
                "target_citation_returned": result.target_citation,
                "checks": [
                    {"name": check.name, "passed": check.passed, "detail": check.detail}
                    for check in result.checks
                ],
                "quotes": [
                    {
                        "text": quote.text,
                        "matches": [format_ref(ref) for ref in quote.matches],
                        "grammar_only": quote.grammar_only,
                    }
                    for quote in result.quotes
                ],
                "usage": result.usage,
                "error": result.error,
                "passed": result.passed,
            }
            for result in results
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--dry-run", action="store_true", help="validate anchors without a model call")
    parser.add_argument("--questions", type=Path, default=QUESTIONS_PATH)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--only", help="comma-separated ids, e.g. A1,B2 (debugging)")
    parser.add_argument("--delay", type=float, default=2.0, help="seconds between questions")
    args = parser.parse_args()

    if not args.questions.is_file():
        print(f"Question set not found: {args.questions}", file=sys.stderr)
        return 2
    if not args.db.is_file():
        print(f"Database not found: {args.db}", file=sys.stderr)
        return 2

    try:
        questions = parse_questions(args.questions)
    except ValueError as exc:
        print(f"Invalid question set: {exc}", file=sys.stderr)
        return 2

    if args.only:
        wanted = [item.strip() for item in args.only.split(",") if item.strip()]
        by_id = {question.id: question for question in questions}
        unknown = [item for item in wanted if item not in by_id]
        if unknown:
            print(f"Unknown question id(s): {', '.join(unknown)}", file=sys.stderr)
            return 2
        questions = [by_id[item] for item in wanted]

    if args.dry_run:
        return dry_run(questions, args.db, VALIDATION_PATH)

    settings = get_settings()
    if not settings.gemini_api_key:
        print(
            "GEMINI_API_KEY is not set. Refusing to fake a run; "
            "use --dry-run to validate the question set.",
            file=sys.stderr,
        )
        return 2

    results, email, stopped_early, meta = asyncio.run(
        run_questions(questions, args.db, args.delay)
    )
    passed = sum(result.passed for result in results)
    groups = Counter(result.question.group for result in results)
    group_passed = Counter(result.question.group for result in results if result.passed)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    stamp = meta["started_at"]
    markdown_path = args.out_dir / f"tutor-run-{stamp}.md"
    json_path = args.out_dir / f"tutor-run-{stamp}.json"
    markdown_path.write_text(render_markdown(meta, results), encoding="utf-8")
    json_path.write_text(
        json.dumps(render_json(meta, results), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print()
    print(
        f"Mechanical checks: {passed}/{len(results)} passed "
        f"(A {group_passed['A']}/{groups['A']}, B {group_passed['B']}/{groups['B']}, "
        f"C {group_passed['C']}/{groups['C']})."
    )
    print("This is not an accuracy score; review the replies in the saved transcript.")
    print(f"Evaluation user: {email}")
    print(f"Saved: {markdown_path}")
    print(f"Saved: {json_path}")
    return 0 if passed == len(results) and not stopped_early else 1


if __name__ == "__main__":
    raise SystemExit(main())
