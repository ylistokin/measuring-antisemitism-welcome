# Measuring Antisemitism — Welcome post: data and code

This repository holds the data, code and reproduction instructions for the three figures in
**"Welcome to Measuring Antisemitism"**, the first post of the Brodie Center for Jewish and Israeli Law
(Yale Law School) blog on empirical studies of antisemitism, by Yair Listokin and Yehonatan Givati.

**Read the post:** <https://ylistokin.github.io/measuring-antisemitism-welcome/>

| Figure | What it shows | Folder |
|---|---|---|
| 1 | Anti-Jewish and anti-Black hate crimes per 100,000 group members, 1991–2025 (FBI) | [`figure1/`](figure1/) |
| 2 | Modern empirical papers on anti-Black racism vs. antisemitism in top-10 journals, 2000–2026, by field | [`figure2/`](figure2/) |
| 3 | Monthly Implicit Association Test D scores, Black/White vs. Jewish/Christian, 2023–2025 (Project Implicit) | [`figure3/`](figure3/) |

<p align="center">
  <img src="figure1/outputs/figure1_hate_crime_per_capita_ajyb.png" width="32%">
  <img src="figure2/outputs/figure_2_modern_top_10_journals.png" width="32%">
  <img src="figure3/outputs/figure3_iat_black_jewish_ci.png" width="32%">
</p>

## Reproduce all three figures

Python 3.10+.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt

python figure1/scripts/make_figure1.py         # -> figure1/outputs/
python figure2/scripts/build_figure2.py        # -> figure2/outputs/
python -m unittest discover -s figure2/tests -v
python figure3/scripts/make_figure3.py         # -> figure3/outputs/
```

These commands start from the small, committed analysis files in each `data/` folder. Each figure's
README also explains how to rebuild those files from the original raw sources (the FBI hate crime file
and the Project Implicit files are each hundreds of megabytes, so they are not committed). A GitHub
Actions workflow ([`.github/workflows/reproduce.yml`](.github/workflows/reproduce.yml)) reruns every
figure on each push.

## Repository layout

```
index.md, _config.yml     the post, served by GitHub Pages
figure1/                  FBI hate crimes per capita
  data/                   annual counts by bias (from Kaplan's FBI file)
  scripts/                build_kaplan_annual.py (raw -> data), make_figure1.py (data -> figure)
  outputs/                figure PNG + per-capita table
figure2/                  journal census (formerly the figure-2-reproducibility repo; history kept)
  data/ prompts/ scripts/ tests/ outputs/
figure3/                  Project Implicit IAT D scores
  data/                   monthly means, SDs, n, SEs
  scripts/                build_iat_monthly.py (raw -> data), make_figure3.py (data -> figure)
  outputs/
```

## Sources

- Jacob Kaplan, *Concatenated FBI UCR/NIBRS Hate Crime Data, 1991–2024*, openICPSR Project 103500 (V12.1).
- FBI Crime Data Explorer, <https://cde.ucr.cjis.gov> (2025 counts, accessed Sept. 29, 2026).
- American Jewish Year Book, "Jewish Population in the United States," Berman Jewish DataBank.
- U.S. Census Bureau and Pew Research Center, "Facts About the U.S. Black Population."
- Crossref / OpenAlex metadata for the journal census (Figure 2).
- Project Implicit demo-site public data: Race IAT and Jewish/Christian IAT, 2023–2025 (OSF).

## Citation and license

See [`CITATION.cff`](CITATION.cff). Code is MIT-licensed ([`LICENSE`](LICENSE)); third-party data remain
subject to their providers' terms.
