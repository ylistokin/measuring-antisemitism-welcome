"""Collapse Jacob Kaplan's concatenated FBI hate crime file to annual counts by bias.

Input : ucr_hate_crimes_1991_2024.csv from openICPSR Project 103500 (V12.1), ~800 MB.
        Not included in this repo; download it from https://www.openicpsr.org/openicpsr/project/103500
Output: figure1/data/kaplan_annual_by_bias.csv

Method: each row with hate_crime_incident_present == "one or more hate crime incidents present"
is one incident. An incident counts toward a bias if ANY of its up-to-10 offenses lists that
bias (so an incident with both anti-Black and anti-Jewish offenses counts in both columns).

Usage: python figure1/scripts/build_kaplan_annual.py path/to/ucr_hate_crimes_1991_2024.csv
"""
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "data" / "kaplan_annual_by_bias.csv"
BIAS_COLS = [f"bias_motivation_offense_{i}" for i in range(1, 11)]
BIASES = {
    "antiblack": "anti-black",
    "antiwhite": "anti-white",
    "antihispanic": "anti-hispanic or latino",
    "antiasian": "anti-asian",
    "antijewish": "anti-jewish",
    "antimuslim": "anti-islamic (muslim)",
    "antigaymen": "anti-gay (male)",
}


def main(src: str) -> None:
    parts = []
    reader = pd.read_csv(src, usecols=["year", "hate_crime_incident_present", *BIAS_COLS],
                         dtype=str, chunksize=500_000)
    for chunk in reader:
        chunk = chunk[chunk["hate_crime_incident_present"] == "one or more hate crime incidents present"]
        bias = chunk[BIAS_COLS]
        out = pd.DataFrame({"year": chunk["year"].astype(int), "total_incidents": 1})
        for col, label in BIASES.items():
            out[col] = bias.eq(label).any(axis=1).astype(int)
        parts.append(out.groupby("year").sum())
    annual = pd.concat(parts).groupby(level=0).sum().reset_index()
    annual.to_csv(OUT, index=False)
    print(annual.to_string(index=False))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
