"""Reproduce Figure 1: hate crimes per 100,000 Jewish and Black Americans, 1991-2025.

Reads figure1/data/kaplan_annual_by_bias.csv; writes figure1/outputs/figure1_hate_crime_per_capita_ajyb.{csv,png}.
"""
import pandas as pd, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
here = Path(__file__).resolve().parent
root = here.parent
out = root / "outputs"
out.mkdir(exist_ok=True)
k = pd.read_csv(root / "data" / "kaplan_annual_by_bias.csv")[["year","antiblack","antijewish"]]
# 2025: FBI Crime Data Explorer (Kaplan file not yet extended to 2025)
k = pd.concat([k, pd.DataFrame([{"year":2025,"antiblack":2847,"antijewish":1540}])], ignore_index=True)
k["incident_source"] = np.where(k.year<=2024, "Kaplan concatenated FBI UCR/NIBRS 1991-2024", "FBI Crime Data Explorer (2025 release)")

# AJYB "Jewish Population in the United States" U.S. totals, Berman Jewish DataBank
ajyb = {1991:5798000,1992:5828000,1993:5840000,1994:5880000,1995:5900000,1996:5900000,
        1997:6005000,1998:6041000,1999:6061000,2000:6136000,2001:6155000,2002:6155000,2003:6155000,
        2006:6452030,2007:6443805,2008:6489110,2010:6544000,2011:6588065,2012:6721680,2013:6721965,
        2014:6768980,2015:6829930,2016:6856304,2017:6850865,2018:6925475,2019:6968600,2020:7153495,
        2021:7266140,2022:7391905,2023:7460600,2024:7699755}
years = list(range(1991,2026))
jp = pd.Series({y: ajyb.get(y, np.nan) for y in years}, dtype=float)
jnote = {y: "AJYB estimate for this year" for y in ajyb}
jnote.update({2004:"interpolated (no AJYB 2004 volume in DataBank)",2005:"interpolated (no AJYB 2005 volume in DataBank)",
              2009:"interpolated (no AJYB 2009 volume in DataBank)",2025:"AJYB 2024 estimate carried forward"})
jp[2025] = ajyb[2024]
jp = jp.interpolate()
# Black population ("alone or in combination"), same benchmarks as original Figure 1, interpolated; 2025 extended at 2023-24 trend
bb = {1991:30.0e6,2000:36.4e6,2010:42.0e6,2020:46.9e6,2023:48.3e6,2024:48.7e6,2025:49.1e6}
bp = pd.Series({y: bb.get(y, np.nan) for y in years}, dtype=float).interpolate()
df = k.set_index("year").loc[years].copy()
df["jewish_pop"] = jp.round(0).astype(int); df["jewish_pop_note"] = [jnote[y] for y in years]
df["black_pop"] = bp.round(0).astype(int)
df["antijewish_per_100k"] = (df.antijewish/df.jewish_pop*1e5).round(2)
df["antiblack_per_100k"] = (df.antiblack/df.black_pop*1e5).round(2)
df["ratio_jewish_to_black"] = (df.antijewish_per_100k/df.antiblack_per_100k).round(2)
df.reset_index().to_csv(out/"figure1_hate_crime_per_capita_ajyb.csv", index=False)

BLUE, ORANGE = "#1f5fa8", "#c65b28"
fig, ax = plt.subplots(figsize=(13, 12.5), dpi=150)
fig.patch.set_facecolor("#fcfcfb"); ax.set_facecolor("#fcfcfb")
x = df.index.values
ax.plot(x, df.antijewish_per_100k, "-o", color=BLUE, lw=2.6, ms=6, label="Anti-Jewish hate crimes / 100,000 Jewish Americans")
ax.plot(x, df.antiblack_per_100k, "-o", color=ORANGE, lw=2.6, ms=6, label="Anti-Black hate crimes / 100,000 Black Americans")
def label(series, color, default_up):
    v = series.values
    for i, (xi, val) in enumerate(zip(x, v)):
        prev = v[i-1] if i > 0 else val; nxt = v[i+1] if i < len(v)-1 else val
        if val < prev and val < nxt: up = False      # local trough: label below
        elif val > prev and val > nxt: up = True     # local peak: label above
        else: up = default_up
        ax.annotate(f"{val:.1f}", (xi, val), xytext=(0, 8 if up else -9), textcoords="offset points",
                    ha="center", va="bottom" if up else "top", fontsize=9.5, color=color, fontweight="bold",
                    bbox=dict(boxstyle="square,pad=0.08", fc="#fcfcfb", ec="none"))
# per-point value labels removed at Yair's request (y axis suffices)
ax.axvspan(2024.5, 2025.5, color="#888", alpha=0.08, lw=0)
ax.set_xlim(1990, 2026); ax.set_ylim(0, 30)
ax.set_xticks(range(1990, 2026, 5)); ax.set_xticks(range(1991, 2026), minor=True)
ax.set_ylabel("Incidents per 100,000 group population", fontsize=15)
ax.tick_params(labelsize=14, colors="#444"); ax.tick_params(which="minor", length=3)
ax.grid(axis="y", color="#e2e2e2"); ax.set_axisbelow(True)
for s in ["top","right"]: ax.spines[s].set_visible(False)
for s in ["left","bottom"]: ax.spines[s].set_color("#888")
ax.legend(loc="upper left", frameon=False, fontsize=19)
fig.suptitle("Figure 1: Hate Crimes per Capita,\nJewish and Black Americans, 1991–2025", x=0.012, ha="left", y=0.99, fontsize=27, linespacing=1.25, fontweight="bold")
import textwrap
paras = [
 "Notes: 2025 (shaded) uses FBI Crime Data Explorer counts, not yet in the Kaplan file; Jewish population for 2025 uses the AJYB 2024 estimate. "
 "All years with FBI hate crime data are plotted. The DataBank has no AJYB estimate for 2004, 2005 or 2009; for those years the Jewish population is interpolated linearly between the AJYB estimates "
 "for the adjacent years (2003 and 2006; 2008 and 2010), which differ by less than 5%. The AJYB volumes for 2002 and 2003 repeat the 2001 estimate (6,155,000). "
 "Black population interpolated between Census benchmarks; 2025 extended at the 2023–24 trend.",
 "[1] Hate crime incidents, 1991–2024 — Jacob Kaplan, Concatenated FBI UCR/NIBRS Hate Crime Data, 1991–2024, openICPSR Project 103500. 2025 — FBI Crime Data Explorer, https://cde.ucr.cjis.gov (accessed Sept. 29, 2026).",
 "[2] Jewish American population — American Jewish Year Book, \"Jewish Population in the United States\" (annual, 1991–2024), Berman Jewish DataBank, https://www.jewishdatabank.org/databank/search-results/?category=U.S.%20National",
 "[3] Black American population (\"alone or in combination\") — U.S. Census Bureau and Pew Research Center, \"Facts About the U.S. Black Population.\""]
notes = "\n".join(textwrap.fill(p_, 112, subsequent_indent="     " if p_.startswith("[") else "") for p_ in paras)
nt = fig.text(0.012, 0.01, notes, fontsize=15, color="#444", ha="left", va="bottom", linespacing=1.5)
fig.canvas.draw()
r = fig.canvas.get_renderer()
nh = nt.get_window_extent(r).height / fig.bbox.height
th = fig._suptitle.get_window_extent(r).y0 / fig.bbox.height
fig.subplots_adjust(left=0.085, right=0.985, top=th-0.025, bottom=nh+0.055)
fig.savefig(out/"figure1_hate_crime_per_capita_ajyb.png", facecolor=fig.get_facecolor())
print(df[["antijewish","jewish_pop","antijewish_per_100k","antiblack","black_pop","antiblack_per_100k","ratio_jewish_to_black"]].to_string())
