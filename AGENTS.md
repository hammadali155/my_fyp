# AGENTS.md

Guidance for AI agents (and humans) working in this repository.

## Project Overview

**AI-Powered Classical Arabic & Quranic Learning Platform** — a Final Year Project (COMSATS University Islamabad, Attock Campus).

The platform helps learners study Classical Arabic (CA) and Quranic linguistics using AI. Key domains from the research and proposal:

- **Morphology (Sarf)**: root-and-pattern word structures; root extraction and diacritization.
- **Syntax (Nahw)**: sentence parsing and grammatical analysis of Quranic verses.
- **Learning/teaching**: verse-based drills, spaced repetition (SM-2 / FSRS), progress tracking.
- **NLP tooling baseline**: CAMeL Tools, MADAMIRA, Farasa for morphological analysis and diacritization.

## Goals & Guardrails

- **Quranic accuracy is paramount.** A single diacritic error can change meaning. NLP/correctness outputs touching the Quranic text must be validated before landing.
- Data: current files are research/proposal artifacts. No code or dataset exists yet. Source directories will be added as the stack is chosen.

## Repository Structure

```
fyp/
├── AGENTS.md                  # this file
├── README.md                  # project overview
├── docs/                      # documentation & artifacts
│   ├── proposal/              # proposal .docx, modules PDF, LaTeX template
│   ├── defense/               # defense presentation materials
│   ├── diagrams/              # model/architecture diagrams
│   └── planning/              # gantt chart, WBS
└── research/                  # papers + literature review summary
```

## Conventions

When starting to write code, record the chosen stack and the commands **here**:
- **Backend Stack**: Python 3.11 managed via `uv`, FastAPI, SQLAlchemy 2.0 (async), Pydantic v2, SQLite (dev) / PostgreSQL (prod).
  - Sync: `cd backend && uv sync`
  - Dev Server: `cd backend && uv run fastapi dev app/main.py`
  - Test: `cd backend && uv run pytest`
  - Lint: `cd backend && uv run ruff check`
  - Typecheck: `cd backend && uv run mypy app`
- **Frontend Stack**: Kotlin Compose Multiplatform (Desktop, Android, iOS, Web) via Amper (`./kotlin`).
  - Build: `./kotlin build`
  - Test: `./kotlin test`
  - Run Desktop: `./kotlin run -m desktopApp`

Until then:

- Prefer tools already in the repo (e.g., LaTeX proposal template, existing docs) over reinventing.
- Match existing naming conventions; spaces in filenames are currently present but prefer `kebab-case` for new files.
- Do not add code comments unless asked.
- Do not commit unless explicitly requested.

## Workflow

- Proposal template lives at `docs/proposal/BS_FYP_Proposal_Template/` (`.tex`).
- Current defense deck: `docs/defense/An-AI-Powered-Classical-Arabic-and-Quranic-Learning-Platform 1.pptx.pdf`.
- Literature review summary: `research/literature-review-summary.txt`.