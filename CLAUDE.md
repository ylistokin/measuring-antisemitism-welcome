# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

Data, code and a GitHub Pages site for the three figures in the "Welcome to Measuring Antisemitism" blog post (Brodie Center, Yale Law School). It is a reproducibility package, not an application: each `figureN/` folder is self-contained (`data/` → `scripts/` → `outputs/`), and `index.md` + `_config.yml` (Jekyll, `minima` theme) are the post itself, embedding images from `figureN/outputs/`.

## Commands

Run from the repository root with the pinned environment (`python -m pip install -r requirements.txt`; Python 3.12 in CI, 3.13 tested).

```bash
python figure1/scripts/make_figure1.py
python figure2/scripts/build_figure2.py
python figure3/scripts/make_figure3.py
python -m unittest discover -s figure2/tests -v                                   # only test suite
python -m unittest figure2.tests.test_figure2.Figure2Tests.test_published_counts   # single test
```

## The core invariant: outputs reproduce exactly

CI (`.github/workflows/reproduce.yml`) reruns every script, then `python check_outputs.py`: text outputs must be byte-identical, PNGs pixel-identical (compressed PNG bytes differ between Windows zlib-ng and Linux zlib, so the script restores pixel-identical PNGs and then requires a clean `git status`), and no untracked file may appear. Run `check_outputs.py` locally after regenerating. Everything is built to make that hold across OSes:
- `requirements.txt` pins every package exactly. Matplotlib versions change layout (3.11 visibly shifts Figure 1), so bumping a pin means regenerating and committing all outputs.
- `.gitattributes` forces LF; scripts write CSVs with `lineterminator="\n"` (pandas and `csv` default to CRLF on Windows) and PNGs with `metadata={"Software": None}`.
- Figure 2's chart is drawn with Pillow using the bundled `figure2/fonts/LiberationSans-*.ttf` — never a system font — and `ImageFont.Layout.BASIC` (Raqm shaping exists only on some platforms and moves glyphs).

After changing any script or input, rerun it and commit the regenerated outputs together with the change.

## Figure 2 pipeline (the non-obvious one)

`figure2/scripts/build_figure2.py` is the single entry point. Inputs: the census workbook `figure2/data/source/*.xlsx` (SHA-256 in `docs/checksums.json`, verified each run — never edit it) and `data/period_exclusions.csv` (24 empirical Class A papers that fail the "at least one observation after 1960" rule, keyed by `record_id`). It regenerates `data/master_census.csv` and the other sheet-export CSVs, the 199-row ledger `data/figure2_papers.csv`, and `outputs/`. Counts are checked against `EXPECTED` (163/12), the workbook's `Figure 2` sheet X2:Z5, and its `By Discipline` sheet. Do not hand-edit generated CSVs; change an inclusion decision by editing `period_exclusions.csv` (and `EXPECTED`, the README tables, and `index.md`'s "more than 13" ratio if counts change).

`record_id` = first 16 hex of SHA-256 of the lower-cased DOI/URL, or `journal|year|title` when there is no DOI.

The upstream census (journal selection, Crossref/OpenAlex harvest, model-assisted coding) has no code; it is documented by `figure2/prompts/` and the workbook. An older "contemporary" specification (151/10) exists only as totals and is intentionally not reproduced.

## Other figures

- **Figure 1**: 1991–2024 counts come from `data/kaplan_annual_by_bias.csv`; 2025 counts and all population series are **hard-coded in `make_figure1.py`**, documented in `figure1/README.md` — keep them in sync. `build_kaplan_annual.py` rebuilds the data from Kaplan's ~800 MB raw file (not committed).
- **Figure 3**: `make_figure3.py` plots monthly means with 95% CIs (mean ± 1.96·se). `build_iat_monthly.py` rebuilds the monthly CSVs from ~1.6 GB of Project Implicit files and needs `requirements-raw.txt` (pyreadstat).

## Conventions

- The post text (`index.md`) is the published essay; change it only to correct a claim against the data.
- Commit messages are short, imperative and professional ("Add …", "Fix …").
