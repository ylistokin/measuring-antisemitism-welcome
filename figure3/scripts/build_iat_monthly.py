"""Build the monthly IAT D-score series behind Figure 3 from Project Implicit's public files.

Raw files are NOT included in this repo (they are ~1.5 GB). Download them from Project Implicit's
public demo-site data on OSF (https://osf.io/y9hiq/; the Jewish/Christian IAT archive
is https://osf.io/tupn8/):
  - JewishIAT.public.2023-2025.sav   (inside JewishIAT.public.2023-2025.zip)
  - RaceIAT.public.2023.sav, RaceIAT.public.2024.sav, Race_IAT.public.2025.csv

Method (both tests)
  * keep sessions dated 2023-01-01 or later with a non-missing overall D score
    (i.e. a completed IAT);
  * drop respondents evaluating their own group:
      - Jewish/Christian IAT: keep ident == 2 ("Do you consider yourself Jewish?" = No);
      - Race IAT: drop raceomb002 == 5 (single-select "Black or African American", used
        Jan-Feb 2023) or raceomb_003_black == 1 (multi-select checkbox, used thereafter);
  * collapse to calendar months: mean, SD, n, SE = SD / sqrt(n). Unweighted.
D scores: D_biep.Christian_Good_all (Jewish/Christian; positive = Christian+good / Jewish+bad)
          D_biep.White_Good_all     (Race; positive = White+good / Black+bad)

Usage:
  python figure3/scripts/build_iat_monthly.py --jewish JewishIAT.public.2023-2025.sav \
      --race RaceIAT.public.2023.sav RaceIAT.public.2024.sav Race_IAT.public.2025.csv
Requires pyreadstat (pip install pyreadstat) for .sav files.
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).resolve().parents[1] / "data"
START = pd.Timestamp("2023-01-01")


def read_any(path: str, cols: list[str]) -> pd.DataFrame:
    if path.endswith(".sav"):
        import pyreadstat
        meta = pyreadstat.read_sav(path, metadataonly=True)[1]
        df, _ = pyreadstat.read_sav(path, usecols=[c for c in cols if c in meta.column_names])
    else:
        header = pd.read_csv(path, nrows=0).columns
        chunks = pd.read_csv(path, usecols=[c for c in cols if c in header], dtype=str,
                             chunksize=200_000)  # chunked: the 2025 Race IAT csv is ~670 MB
        df = pd.concat(chunks, ignore_index=True)
    for c in cols:
        if c not in df:
            df[c] = np.nan
    df["date"] = pd.to_datetime(df["date"], errors="coerce", format="mixed")  # some rows lack a time
    return df


def monthly(df: pd.DataFrame, dcol: str) -> pd.DataFrame:
    df = df[(df["date"] >= START) & df[dcol].notna()]
    g = df.groupby(df["date"].dt.to_period("M"))[dcol]
    out = pd.DataFrame({"d_mean": g.mean(), "d_std": g.std(), "n": g.size()})
    out["se"] = out["d_std"] / np.sqrt(out["n"])
    out.index = out.index.to_timestamp()
    out.index.name = "month"
    return out.reset_index()


def jewish(path: str) -> pd.DataFrame:
    d = "D_biep.Christian_Good_all"
    df = read_any(path, ["date", d, "ident"])
    df[d] = pd.to_numeric(df[d], errors="coerce")
    df = df[pd.to_numeric(df["ident"], errors="coerce") == 2]
    return monthly(df, d)


def race(paths: list[str]) -> pd.DataFrame:
    d = "D_biep.White_Good_all"
    frames = []
    for p in paths:
        df = read_any(p, ["date", d, "raceomb002", "raceomb_003_black"])
        df[d] = pd.to_numeric(df[d], errors="coerce")
        black = (pd.to_numeric(df["raceomb002"], errors="coerce") == 5) | \
                (pd.to_numeric(df["raceomb_003_black"], errors="coerce") == 1)
        frames.append(df.loc[~black, ["date", d]])
    return monthly(pd.concat(frames, ignore_index=True), d)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--jewish", help="Jewish/Christian IAT .sav or .csv")
    ap.add_argument("--race", nargs="+", help="Race IAT files (.sav or .csv), any order")
    a = ap.parse_args()
    if a.jewish:
        j = jewish(a.jewish)
        j.to_csv(DATA / "jewish_iat_monthly_nonjewish.csv", index=False)
        print("Jewish/Christian:", len(j), "months,", int(j.n.sum()), "sessions")
    if a.race:
        r = race(a.race)
        r.to_csv(DATA / "race_iat_monthly_nonblack.csv", index=False)
        print("Race:", len(r), "months,", int(r.n.sum()), "sessions")
