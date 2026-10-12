"""Reproduce Figure 3: monthly IAT D scores for Blacks and Jews, 2023-2025, with 95% CIs.

Reads  figure3/data/race_iat_monthly_nonblack.csv and figure3/data/jewish_iat_monthly_nonjewish.csv
       (built from Project Implicit raw files by build_iat_monthly.py).
Writes figure3/outputs/figure3_iat_black_jewish_ci.png
"""
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)

race = pd.read_csv(ROOT / "data" / "race_iat_monthly_nonblack.csv", parse_dates=["month"])
jew = pd.read_csv(ROOT / "data" / "jewish_iat_monthly_nonjewish.csv", parse_dates=["month"])
for d in (race, jew):
    d["lo"] = d.d_mean - 1.96 * d.se
    d["hi"] = d.d_mean + 1.96 * d.se

BLUE, ORANGE, BG = "#2272d6", "#ec6233", "#fcfcfb"
fig, ax = plt.subplots(figsize=(12.95, 12.9), dpi=200)
fig.patch.set_facecolor(BG); ax.set_facecolor(BG)

ax.fill_between(race.month, race.lo, race.hi, color=BLUE, alpha=0.18, lw=0, label="95% CI, Black/White")
ax.fill_between(jew.month, jew.lo, jew.hi, color=ORANGE, alpha=0.18, lw=0, label="95% CI, Jewish/Christian")
ax.plot(race.month, race.d_mean, color=BLUE, lw=2.6, label="Black/White IAT (non-Black respondents)")
ax.plot(jew.month, jew.d_mean, color=ORANGE, lw=2.6, label="Jewish/Christian IAT (non-Jewish respondents)")
for d, c in ((race, BLUE), (jew, ORANGE)):
    ax.annotate(f"{d.d_mean.iloc[-1]:.2f}", (d.month.iloc[-1], d.d_mean.iloc[-1]), xytext=(10, 0),
                textcoords="offset points", va="center", color=c, fontsize=17, fontweight="bold")

ax.set_ylim(0.20, 0.45)
ax.set_yticks([0.20, 0.25, 0.30, 0.35, 0.40, 0.45])
ax.yaxis.set_major_formatter(plt.FormatStrFormatter("%.2f"))
ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[2, 8]))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
ax.set_ylabel("Mean D score (monthly)", fontsize=16, color="#444")
ax.tick_params(labelsize=16, colors="#444", length=0)
ax.grid(axis="y", color="#dddddd"); ax.set_axisbelow(True)
for s in ax.spines.values():
    s.set_visible(False)
h, l = ax.get_legend_handles_labels()
order = [2, 3, 0, 1]  # lines in left column, CI bands in right column
ax.legend([h[i] for i in order], [l[i] for i in order], loc="upper left", ncol=2, frameon=False,
          fontsize=15, labelcolor="#444", columnspacing=2.5)

fig.text(0.015, 0.975, "Figure 3: Implicit Association Test \"D\" Scores for Blacks and Jews, 2023-2025",
         fontsize=20, fontweight="bold", va="top")
fig.text(0.045, 0.94, "Monthly means with 95% confidence intervals, excluding Black and Jewish Respondents "
         "evaluating their own group", fontsize=14.5, color="#444", va="top")

n_race, n_jew = int(race.n.sum()), int(jew.n.sum())
sep = jew.loc[jew.month == "2025-09-01", "n"]
note = (
    "Notes: D scores are the standardized Implicit Association Test measure (Greenwald, Nosek & Banaji 2003); "
    "higher values indicate a stronger average implicit preference for White over Black people (blue) or for "
    "Christian over Jewish people (orange) among the respondents included. Respondents who self-identified as "
    "Black were excluded from the Black/White series; respondents who self-identified as Jewish were excluded "
    "from the Jewish/Christian series -- so both series reflect only the non-target-group share of Project "
    "Implicit's self-selected demo-site test-takers, not a representative sample of the U.S. population. "
    "Shaded bands are 95% confidence intervals for each monthly mean (mean ± 1.96 × SD/√n). "
    "Bands for the Black/White series are narrow because monthly samples are large (roughly "
    f"{round(race.n.min(), -3):,}-{round(race.n.max(), -3):,}); bands for the Jewish/Christian series are wider "
    f"because monthly samples are smaller (roughly {round(jew.n.min(), -2):,}-{round(jew.n.max(), -3):,}"
    + (f"; the September 2025 sample is only {int(sep.iloc[0])}" if len(sep) else "") + "). "
    f"Underlying sample sizes: roughly {n_race:,} completed Black/White IATs and {n_jew:,} completed "
    "Jewish/Christian IATs, summed across all months shown. Source: Project Implicit demo-site public data files "
    "(Race IAT and Jewish/Christian IAT), 2023-2025. Monthly means, unweighted. Data as currently released run "
    "through December 2025. Jewish/Christian IAT data begin May 2023 (earliest available); Black/White IAT data "
    "begin January 2023."
)
fig.text(0.045, 0.012, textwrap.fill(note, 128), fontsize=11.5, color="#444", va="bottom", linespacing=1.45)
fig.subplots_adjust(left=0.085, right=0.92, top=0.905, bottom=0.235)
fig.savefig(OUT / "figure3_iat_black_jewish_ci.png", facecolor=BG)
print(f"Wrote {OUT / 'figure3_iat_black_jewish_ci.png'}; final values: Black {race.d_mean.iloc[-1]:.3f}, "
      f"Jewish {jew.d_mean.iloc[-1]:.3f}")
