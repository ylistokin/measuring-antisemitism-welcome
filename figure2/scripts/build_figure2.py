"""Build Figure 2 from the census workbook.

One command, run from the repository root:

    python figure2/scripts/build_figure2.py

Steps
  1. Verify the SHA-256 of data/source/<workbook>.xlsx against docs/checksums.json.
  2. Export the workbook's census sheets to data/*.csv (readable copies of the source).
  3. Select every Master Census record coded Class A and Empirical (199 records).
  4. Apply the 24 adjudicated pre-1960 exclusions in data/period_exclusions.csv and
     write the paper-level ledger data/figure2_papers.csv.
  5. Count included papers by field and subject, and check the counts against EXPECTED,
     the workbook's own Figure 2 sheet (X2:Z5) and its By Discipline sheet.
  6. Write outputs/figure_2_counts.csv and the chart (PNG and SVG).

All outputs are deterministic: rerunning reproduces the committed CSV/SVG files byte for byte and the PNG pixel for pixel.
"""

import csv
import hashlib
import html
import json
import textwrap
from collections import Counter
from pathlib import Path

import openpyxl
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
WORKBOOK = DATA / "source" / "racism_antisemitism_census_with_modern_figure_2.xlsx"
EXCLUSIONS = DATA / "period_exclusions.csv"
LEDGER = DATA / "figure2_papers.csv"
CHECKSUMS = ROOT / "docs" / "checksums.json"
FONTS = ROOT / "fonts"
OUTPUT_DIR = ROOT / "outputs"

DISCIPLINES = ["Economics", "Political Science", "Psychology", "Sociology"]
SUBJECTS = ["Anti-Black", "Antisemitism"]
EXPECTED = {
    ("Economics", "Anti-Black"): 27,
    ("Economics", "Antisemitism"): 2,
    ("Political Science", "Anti-Black"): 13,
    ("Political Science", "Antisemitism"): 4,
    ("Psychology", "Anti-Black"): 46,
    ("Psychology", "Antisemitism"): 2,
    ("Sociology", "Anti-Black"): 77,
    ("Sociology", "Antisemitism"): 4,
}
# Workbook sheet -> exported CSV. Each sheet has a title block; the column header is on row 5.
SHEET_EXPORTS = {
    "Master Census": "master_census.csv",
    "Journal Universe": "journal_universe.csv",
    "Codebook": "codebook.csv",
    "Search Log": "search_log.csv",
    "Completeness": "completeness.csv",
    "By Discipline": "by_discipline.csv",
}
HEADER_ROW = 5
LEDGER_FIELDS = ["record_id", "discipline", "journal", "publication_year", "authors", "title", "doi_url",
                 "subject", "class", "empirical_status", "population_country", "include_figure2", "period_decision"]
INCLUDED_NOTE = "Includes at least one empirical observation after 1960."
EXCLUDED_NOTE = "Excluded: no qualifying empirical observation after 1960 was identified."


# ---------------------------------------------------------------- data pipeline

def write_csv(path: Path, header: list[str], rows: list[list] | list[dict]) -> None:
    """UTF-8, LF line endings, so the bytes are identical on every OS."""
    with path.open("w", encoding="utf-8", newline="") as f:
        if rows and isinstance(rows[0], dict):
            writer = csv.DictWriter(f, fieldnames=header, lineterminator="\n")
            writer.writeheader()
        else:
            writer = csv.writer(f, lineterminator="\n")
            writer.writerow(header)
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def verify_workbook() -> None:
    expected = json.loads(CHECKSUMS.read_text(encoding="utf-8"))[WORKBOOK.relative_to(ROOT).as_posix()]
    actual = hashlib.sha256(WORKBOOK.read_bytes()).hexdigest()
    if actual != expected:
        raise ValueError(f"{WORKBOOK.name} does not match docs/checksums.json ({actual} != {expected})")


def sheet_table(sheet) -> tuple[list[str], list[list[str]]]:
    rows = list(sheet.iter_rows(min_row=HEADER_ROW, values_only=True))
    header = [c for c in rows[0] if c is not None]
    body = [["" if c is None else str(c) for c in row[:len(header)]] for row in rows[1:]]
    while body and not any(body[-1]):
        body.pop()
    return header, body


def stable_id(row: dict) -> str:
    """Record identifier derived from the DOI/URL, or from journal|year|title when there is none."""
    key = row.get("DOI / URL") or f"{row.get('Journal')}|{row.get('Year')}|{row.get('Title')}"
    return hashlib.sha256(str(key).strip().lower().encode("utf-8")).hexdigest()[:16]


def build_ledger(master: list[dict]) -> list[dict]:
    exclusions = read_csv(EXCLUSIONS)
    excluded_ids = {row["record_id"] for row in exclusions}
    candidates = [r for r in master if r["Class"] == "A" and r["Empirical status"] == "Empirical"]
    ids = {stable_id(r): r for r in candidates}
    for row in exclusions:
        match = ids.get(row["record_id"])
        if match is None or match["Title"] != row["title"]:
            raise ValueError(f"Exclusion does not match an empirical Class A record: {row['title']!r}")
    ledger = []
    for r in candidates:
        included = stable_id(r) not in excluded_ids
        ledger.append({
            "record_id": stable_id(r),
            "discipline": r["Discipline"],
            "journal": r["Journal"],
            "publication_year": r["Year"],
            "authors": r["Authors"],
            "title": r["Title"],
            "doi_url": r["DOI / URL"],
            "subject": r["Subject"],
            "class": r["Class"],
            "empirical_status": r["Empirical status"],
            "population_country": r["Population / country"],
            "include_figure2": str(included).lower(),
            "period_decision": INCLUDED_NOTE if included else EXCLUDED_NOTE,
        })
    return ledger


def check_against_workbook(workbook, master: list[dict], counts: dict) -> None:
    sheet_counts = list(workbook["Figure 2"].iter_rows(min_row=2, max_row=5, min_col=24, max_col=26, values_only=True))
    ours = [(d, counts[(d, "Anti-Black")], counts[(d, "Antisemitism")]) for d in DISCIPLINES]
    if sheet_counts != ours:
        raise ValueError(f"Counts differ from the workbook's Figure 2 sheet: {sheet_counts} != {ours}")
    empirical_a = Counter((r["Discipline"], r["Subject"]) for r in master
                          if r["Class"] == "A" and r["Empirical status"] == "Empirical")
    _, by_discipline = sheet_table(workbook["By Discipline"])
    for discipline, subject, *_rest, empirical_a_only in (row[:5] for row in by_discipline):
        if empirical_a[(discipline, subject)] != int(empirical_a_only):
            raise ValueError(f"Master Census disagrees with By Discipline for {discipline}/{subject}")


def load_data() -> list[dict]:
    """Read the committed ledger, with include_figure2 as a bool."""
    data = read_csv(LEDGER)
    if len({row["record_id"] for row in data}) != len(data):
        raise ValueError("record_id values must be unique")
    for row in data:
        if row["include_figure2"] not in {"true", "false"}:
            raise ValueError("include_figure2 must contain only true/false values")
        row["include_figure2"] = row["include_figure2"] == "true"
    return data


def figure_counts(data: list[dict]) -> dict[tuple[str, str], int]:
    counts = Counter(
        (row["discipline"], row["subject"])
        for row in data
        if row["include_figure2"] in (True, "true") and row["class"] == "A" and row["empirical_status"] == "Empirical"
    )
    observed = {(d, s): counts[(d, s)] for d in DISCIPLINES for s in SUBJECTS}
    if observed != EXPECTED:
        raise ValueError(f"Counts do not match the published Figure 2: {observed}")
    return observed


# ---------------------------------------------------------------- chart

def font(size: int, bold: bool = False, italic: bool = False):
    style = "BoldItalic" if bold and italic else "Bold" if bold else "Italic" if italic else "Regular"
    # BASIC layout: Pillow uses Raqm text shaping only where libraqm is installed, which would make
    # glyph placement depend on the machine.
    return ImageFont.truetype(str(FONTS / f"LiberationSans-{style}.ttf"), size=size,
                              layout_engine=ImageFont.Layout.BASIC)


def centered(draw, xy, text, text_font, fill):
    box = draw.textbbox((0, 0), text, font=text_font)
    draw.text((xy[0] - (box[2] - box[0]) / 2, xy[1]), text, font=text_font, fill=fill)


def render_png(counts, path: Path) -> None:
    width, height = 2800, 2050
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    navy, gray, light = "#17324D", "#606060", "#D1D5DB"
    blue, orange = "#0B7DB8", "#D95F02"
    draw.text((28, 38), "Figure 2: Modern Empirical Papers in Top-10 Journals, by Field", font=font(64, bold=True), fill=navy)
    draw.line((28, 148, width - 28, 148), fill="#9FB6C9", width=2)
    left, right, top, bottom = 190, width - 80, 285, 1740
    for tick in range(0, 101, 20):
        y = bottom - (bottom - top) * tick / 100
        for x in range(left, right, 20):
            draw.line((x, y, min(x + 10, right), y), fill=light, width=2)
        box = draw.textbbox((0, 0), str(tick), font=font(30))
        draw.text((left - 28 - (box[2] - box[0]), y - 18), str(tick), font=font(30), fill=gray)
    category_width = (right - left) / len(DISCIPLINES)
    bar_width = 155
    for index, discipline in enumerate(DISCIPLINES):
        center_x = left + category_width * (index + 0.5)
        for subject, offset, color in (("Anti-Black", -bar_width / 2, blue), ("Antisemitism", bar_width / 2, orange)):
            value = counts[(discipline, subject)]
            y = bottom - (bottom - top) * value / 100
            x0 = center_x + offset - bar_width / 2
            draw.rectangle((x0, y, x0 + bar_width, bottom), fill=color)
        centered(draw, (center_x, bottom + 24), discipline, font(36), gray)
    label_layer = Image.new("RGBA", (500, 70), (255, 255, 255, 0))
    ImageDraw.Draw(label_layer).text((0, 0), "Total empirical papers", font=font(36), fill=gray)
    label_layer = label_layer.rotate(90, expand=True)
    image.paste(label_layer, (25, int((top + bottom - label_layer.height) / 2)), label_layer)
    legend_y, legend_x = 205, (width - 580) / 2
    draw.rectangle((legend_x, legend_y + 10, legend_x + 24, legend_y + 34), fill=blue)
    draw.text((legend_x + 36, legend_y), "Anti-Black", font=font(38), fill=gray)
    second_x = legend_x + 300
    draw.rectangle((second_x, legend_y + 10, second_x + 24, legend_y + 34), fill=orange)
    draw.text((second_x + 36, legend_y), "Antisemitism", font=font(38), fill=gray)
    note = ("Modern means the study includes at least one empirical observation after 1960. Studies may begin before 1960. "
            "Counts include empirical papers in the Top-10 journals for each field where anti-Black racism or antisemitism "
            "is the primary focus. Publication coverage is January 1, 2000–September 18, 2026; 2026 is partial.")
    y = 1840
    for line in textwrap.wrap(note, width=145):
        draw.text((28, y), line, font=font(32, italic=True), fill="#4B5563")
        y += 43
    image.save(path, dpi=(200, 200))


def render_svg(counts, path: Path) -> None:
    family = 'font-family="Liberation Sans, Arial, Helvetica, sans-serif"'
    width, height = 1400, 1025
    left, right, top, bottom = 95, 1360, 142, 870
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
             '<rect width="100%" height="100%" fill="white"/>',
             f'<text x="14" y="54" {family} font-size="32" font-weight="700" fill="#17324D">Figure 2: Modern Empirical Papers in Top-10 Journals, by Field</text>',
             '<line x1="14" y1="74" x2="1386" y2="74" stroke="#9FB6C9"/>']
    for tick in range(0, 101, 20):
        y = bottom - (bottom - top) * tick / 100
        parts += [f'<line x1="{left}" y1="{y}" x2="{right}" y2="{y}" stroke="#D1D5DB" stroke-dasharray="4 4"/>',
                  f'<text x="{left - 18}" y="{y + 6}" text-anchor="end" {family} font-size="16" fill="#606060">{tick}</text>']
    category_width, bar_width = (right - left) / len(DISCIPLINES), 78
    for index, discipline in enumerate(DISCIPLINES):
        cx = left + category_width * (index + 0.5)
        for subject, offset, color in (("Anti-Black", -bar_width / 2, "#0B7DB8"), ("Antisemitism", bar_width / 2, "#D95F02")):
            value = counts[(discipline, subject)]
            y = bottom - (bottom - top) * value / 100
            x = cx + offset - bar_width / 2
            parts.append(f'<rect x="{x}" y="{y}" width="{bar_width}" height="{bottom-y}" fill="{color}"/>')
        parts.append(f'<text x="{cx}" y="{bottom + 32}" text-anchor="middle" {family} font-size="18" fill="#606060">{html.escape(discipline)}</text>')
    parts += [f'<text x="42" y="510" transform="rotate(-90 42 510)" text-anchor="middle" {family} font-size="18" fill="#606060">Total empirical papers</text>',
              f'<rect x="555" y="98" width="12" height="12" fill="#0B7DB8"/><text x="574" y="110" {family} font-size="19" fill="#606060">Anti-Black</text>',
              f'<rect x="700" y="98" width="12" height="12" fill="#D95F02"/><text x="719" y="110" {family} font-size="19" fill="#606060">Antisemitism</text>',
              f'<text x="14" y="942" {family} font-size="15" font-style="italic" fill="#4B5563">Modern means the study includes at least one empirical observation after 1960. Studies may begin before 1960.</text>',
              f'<text x="14" y="968" {family} font-size="15" font-style="italic" fill="#4B5563">Counts include empirical papers in the Top-10 journals for each field where anti-Black racism or antisemitism is the primary focus.</text>',
              f'<text x="14" y="994" {family} font-size="15" font-style="italic" fill="#4B5563">Publication coverage is January 1, 2000–September 18, 2026; 2026 is partial.</text>', '</svg>']
    path.write_text("\n".join(parts) + "\n", encoding="utf-8", newline="\n")


# ---------------------------------------------------------------- main

def main() -> None:
    verify_workbook()
    workbook = openpyxl.load_workbook(WORKBOOK, data_only=True, read_only=False)
    for sheet_name, filename in SHEET_EXPORTS.items():
        header, body = sheet_table(workbook[sheet_name])
        write_csv(DATA / filename, header, body)
    master = read_csv(DATA / "master_census.csv")
    write_csv(LEDGER, LEDGER_FIELDS, build_ledger(master))
    counts = figure_counts(load_data())
    check_against_workbook(workbook, master, counts)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(OUTPUT_DIR / "figure_2_counts.csv", ["Discipline", *SUBJECTS],
              [[d, *(counts[(d, s)] for s in SUBJECTS)] for d in DISCIPLINES])
    render_png(counts, OUTPUT_DIR / "figure_2_modern_top_10_journals.png")
    render_svg(counts, OUTPUT_DIR / "figure_2_modern_top_10_journals.svg")
    black, jewish = (sum(counts[(d, s)] for d in DISCIPLINES) for s in SUBJECTS)
    print(f"Figure 2: {black} anti-Black vs {jewish} antisemitism papers (ratio {black / jewish:.2f})")


if __name__ == "__main__":
    main()
