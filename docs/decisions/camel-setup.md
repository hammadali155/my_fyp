# Decision Memo: CAMeL Tools Setup

**Status:** Research complete. Approved to install on approval. Date: 2026-10-04.

## Python version

- `camel-tools` 1.6.0 supports **Python 3.11–3.14 (64-bit)**. Current repo Python (3.11.17) works; upgrading to 3.12 is supported.

## Package

- PyPI wheel `camel_tools-1.6.0-py3-none-any.whl` (~126 kB) plus Python deps (torch, transformers, dill, kenlm, etc. — several hundred MB).
- Build/runtime requirements:
  - Linux/macOS: `cmake`, `libboost-all-dev`, Rust compiler.
  - Windows 10: `pip install camel-tools -f https://download.pytorch.org/whl/torch_stable.html`; Dialect-ID component not available there.

## Data package

- **`morphology-db-msa-r13`** — SQLite morphology DB for MSA used by `camel_tools.morphology` Analyzer.
- Download size: **40.5 MB**; installed under `~/.camel_tools` by default (override with `CAMELTOOLS_DATA`).
- License: **GPL v2** — do not redistribute; same class of concern as corpus.quran.com morphology.
- `camel_data -i light` = this DB + `disambig-mle-calima-msa-r13` (88.7 MB); `-i defaults` is broader.

## Memory use

- Not documented. The DB loads lazily on first `MorphologyDB`/`Analyzer` construction; budget a few hundred MB–~1 GB per process. Keep the Analyzer as a singleton, not per-request.

## Platforms

- **Linux**: supported (Ubuntu/Debian: `sudo apt-get install cmake libboost-all-dev` + rustup).
- **WSL2**: supported (treated as Linux).
- **Windows 10**: supported for morphology; heavier setup via PyTorch index.

## Approved commands (after your go-ahead)

```bash
sudo apt-get install -y cmake libboost-all-dev
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh   # if rustc missing
cd backend
uv add camel-tools
uv run camel_data -i morphology-db-msa-r13
```

Expected downloads: camel-tools ~0.13 MB wheel; Python deps several hundred MB; morphology DB 40.5 MB.

## Install result 2026-10-04

Installed on Arch Linux (WSL2): `camel-tools 1.6.0`, `camel-kenlm 2026.2.7`,
`torch 2.14.1+cpu` (pinned to the PyTorch CPU index to avoid ~2.4 GB of
CUDA/nvidia wheels — initial CUDA resolution was aborted after repeated
download failures). Morphology DB `morphology-db-msa-r13` downloaded (40.5 MB)
to `~/.camel_tools`. Verified with a real call: `Analyzer(MorphologyDB.builtin_db()).analyze('كتب')`
returned 8 analyses (root ك.ت.ب, pos noun for the first). Tests: 80 passed,
ruff clean, mypy clean. Build prerequisites (cmake/boost/rust) were NOT
needed for the wheel path on this machine.

`camel-tools`/`torch` moved to the optional `nlp` dependency group, so the
base `uv sync` (and the test suite) no longer require them:
- base: `uv sync`
- with NLP stack: `uv sync --extra nlp`
`scripts/camel_smoke.py` exercises the analyzer on 5 words from our `words`
table. Real analysis keys: `root`, `pattern`, `pos`, plus `lex`, `gloss`,
`stem`, `ud`, `vox`, `asp`, `mod`, `per`, `num`, `gen`, `cas`, `form_gen`,
`form_num`, `prc0..3`, `enc0`, segment columns (`d1seg`/`d2seg`/`d3seg`,
`d1tok`...), `lex_logprob`/`pos_logprob`. No top-level `lemma` key — the
lemma is `lex`.
