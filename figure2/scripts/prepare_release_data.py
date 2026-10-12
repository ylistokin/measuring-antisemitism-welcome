"""Create the released plotting CSV from the adjudicated empirical-A JSON export.

This curator utility is not needed for ordinary figure reproduction. It records
the final period adjudications that distinguish the broader modern specification.
"""

import argparse
import csv
import hashlib
import json
from pathlib import Path


EXCLUDED_TITLES = {
    "Colorism, Complexion Homogamy, and Household Wealth: Some Historical Evidence",
    "Segregation and Homeownership in the Early Twentieth Century",
    "Racial Segregation in Housing Markets and the Erosion of Black Wealth",
    "Shocking Racial Attitudes: Black G.I.s in Europe",
    "Racial Discrimination and the Social Contract: Evidence from U.S. Army Enlistment During WWII",
    "The Costs of Employment Segregation: Evidence from the Federal Government Under Woodrow Wilson",
    "Religion, Division of Labor, and Conflict: Anti-Semitism in Germany over 600 Years",
    "Middleman Minorities and Ethnic Violence: Anti-Jewish Pogroms in the Russian Empire",
    "Persecution Perpetuated: The Medieval Origins of Anti-Semitic Violence in Nazi Germany*",
    "The Refugee’s Dilemma: Evidence from Jewish Migration out of Nazi Germany",
    "“Judge Lynch” in the Court of Public Opinion: Publicity and the De-legitimation of Lynching",
    "Deadly Communities: Local Political Milieus and the Persecution of Jews in Occupied Poland",
    "The Diffusion of Exclusion: Medieval Expulsions of Jews",
    "Constructing Interethnic Conflict and Cooperation: Why Some People Harmed Jews and Others Helped Them during the Holocaust in Romania",
    "The Phoenix Effect of State Repression: Jewish Resistance during the Holocaust",
    "Religious Minorities and Resistance to Genocide: The Collective Rescue of Jews in the Netherlands during the Holocaust",
    "Skin-Tone Trauma: Historical and Contemporary Influences on the Health and Interpersonal Outcomes of African Americans",
    "The Colonial History of Systemic Racism: Insights for Psychological Science",
    "Targeting Lynch Victims",
    "The Historical Demography of Racial Segregation",
    "Race, Gender, and the Rape-Lynching Nexus in the U.S. South, 1881-1930",
    "Racial Segregation under Slavery",
    "Exoduster Entrepreneurs: Distinctiveness and Segregation in Minority Communities",
    "Bloodlines: National Border Crossings and Antisemitism in Weimar Germany",
}


def stable_id(row: dict) -> str:
    key = row.get("DOI / URL") or f"{row.get('Journal')}|{row.get('Year')}|{row.get('Title')}"
    return hashlib.sha256(str(key).strip().lower().encode("utf-8")).hexdigest()[:16]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json", type=Path)
    parser.add_argument("output_csv", type=Path)
    args = parser.parse_args()
    records = json.loads(args.input_json.read_text(encoding="utf-8"))
    output = []
    for row in records:
        title = row["Title"]
        included = title not in EXCLUDED_TITLES
        output.append({
            "record_id": stable_id(row),
            "discipline": row["Discipline"],
            "journal": row["Journal"],
            "publication_year": row["Year"],
            "authors": row["Authors"],
            "title": title,
            "doi_url": row["DOI / URL"],
            "subject": row["Subject"],
            "class": row["Class"],
            "empirical_status": row["Empirical status"],
            "population_country": row["Population / country"],
            "include_figure2": str(included).lower(),
            "period_decision": (
                "Includes at least one empirical observation after 1960."
                if included else
                "Excluded: no qualifying empirical observation after 1960 was identified."
            ),
        })
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.output_csv.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(output[0]))
        writer.writeheader()
        writer.writerows(output)


if __name__ == "__main__":
    main()
