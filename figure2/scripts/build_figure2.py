"""Validate the released coding data and reproduce Figure 2."""

import csv
import html
import textwrap
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "figure2_papers.csv"
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


def load_data() -> list[dict]:
    with DATA_PATH.open(encoding="utf-8-sig", newline="") as f:
        data = list(csv.DictReader(f))
    required = {"record_id", "discipline", "subject", "class", "empirical_status", "include_figure2", "period_decision"}
    missing = required.difference(data[0] if data else {})
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    if len({row["record_id"] for row in data}) != len(data):
        raise ValueError("record_id values must be unique")
    for row in data:
        value = row["include_figure2"].lower()
        if value not in {"true", "false"}:
            raise ValueError("include_figure2 must contain only true/false values")
        row["include_figure2"] = value == "true"
    return data


def figure_counts(data: list[dict]) -> dict[tuple[str, str], int]:
    counts = Counter(
        (row["discipline"], row["subject"])
        for row in data
        if row["include_figure2"] and row["class"] == "A" and row["empirical_status"] == "Empirical"
    )
    observed = {(d, s): counts[(d, s)] for d in DISCIPLINES for s in SUBJECTS}
    if observed != EXPECTED:
        raise ValueError(f"Counts do not match the released Figure 2: {observed}")
    return observed


def font(size: int, bold: bool = False, italic: bool = False):
    suffix = "bolditalic" if bold and italic else "bold" if bold else "italic" if italic else "regular"
    candidates = {
        "regular": [Path("C:/Windows/Fonts/arial.ttf"), Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")],
        "bold": [Path("C:/Windows/Fonts/arialbd.ttf"), Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")],
        "italic": [Path("C:/Windows/Fonts/ariali.ttf"), Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf")],
        "bolditalic": [Path("C:/Windows/Fonts/arialbi.ttf"), Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf")],
    }[suffix]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default(size=size)


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
    width, height = 1400, 1025
    left, right, top, bottom = 95, 1360, 142, 870
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
             '<rect width="100%" height="100%" fill="white"/>',
             '<text x="14" y="54" font-family="Arial" font-size="32" font-weight="700" fill="#17324D">Figure 2: Modern Empirical Papers in Top-10 Journals, by Field</text>',
             '<line x1="14" y1="74" x2="1386" y2="74" stroke="#9FB6C9"/>']
    for tick in range(0, 101, 20):
        y = bottom - (bottom - top) * tick / 100
        parts += [f'<line x1="{left}" y1="{y}" x2="{right}" y2="{y}" stroke="#D1D5DB" stroke-dasharray="4 4"/>',
                  f'<text x="{left - 18}" y="{y + 6}" text-anchor="end" font-family="Arial" font-size="16" fill="#606060">{tick}</text>']
    category_width, bar_width = (right - left) / len(DISCIPLINES), 78
    for index, discipline in enumerate(DISCIPLINES):
        cx = left + category_width * (index + 0.5)
        for subject, offset, color in (("Anti-Black", -bar_width / 2, "#0B7DB8"), ("Antisemitism", bar_width / 2, "#D95F02")):
            value = counts[(discipline, subject)]
            y = bottom - (bottom - top) * value / 100
            x = cx + offset - bar_width / 2
            parts.append(f'<rect x="{x}" y="{y}" width="{bar_width}" height="{bottom-y}" fill="{color}"/>')
        parts.append(f'<text x="{cx}" y="{bottom + 32}" text-anchor="middle" font-family="Arial" font-size="18" fill="#606060">{html.escape(discipline)}</text>')
    parts += ['<text x="42" y="510" transform="rotate(-90 42 510)" text-anchor="middle" font-family="Arial" font-size="18" fill="#606060">Total empirical papers</text>',
              '<rect x="555" y="98" width="12" height="12" fill="#0B7DB8"/><text x="574" y="110" font-family="Arial" font-size="19" fill="#606060">Anti-Black</text>',
              '<rect x="700" y="98" width="12" height="12" fill="#D95F02"/><text x="719" y="110" font-family="Arial" font-size="19" fill="#606060">Antisemitism</text>',
              '<text x="14" y="942" font-family="Arial" font-size="15" font-style="italic" fill="#4B5563">Modern means the study includes at least one empirical observation after 1960. Studies may begin before 1960.</text>',
              '<text x="14" y="968" font-family="Arial" font-size="15" font-style="italic" fill="#4B5563">Counts include empirical papers in the Top-10 journals for each field where anti-Black racism or antisemitism is the primary focus.</text>',
              '<text x="14" y="994" font-family="Arial" font-size="15" font-style="italic" fill="#4B5563">Publication coverage is January 1, 2000–September 18, 2026; 2026 is partial.</text>', '</svg>']
    path.write_text("\n".join(parts), encoding="utf-8")


def write_counts(counts) -> None:
    with (OUTPUT_DIR / "figure_2_counts.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Discipline", *SUBJECTS])
        for discipline in DISCIPLINES:
            writer.writerow([discipline, *(counts[(discipline, s)] for s in SUBJECTS)])


if __name__ == "__main__":
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    result = figure_counts(load_data())
    write_counts(result)
    render_png(result, OUTPUT_DIR / "figure_2_modern_top_10_journals.png")
    render_svg(result, OUTPUT_DIR / "figure_2_modern_top_10_journals.svg")
