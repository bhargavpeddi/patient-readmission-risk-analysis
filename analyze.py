"""Validate encounters, run SQL EDA, and build a local HTML summary."""

from __future__ import annotations

import argparse
import csv
import html
import sqlite3
from pathlib import Path

from generate_data import DEPARTMENTS, DIAGNOSES, FIELDS, write_csv


def validate(row: dict[str, str]) -> None:
    if set(row) != set(FIELDS):
        raise ValueError("Unexpected input columns")
    if row["department"] not in DEPARTMENTS or row["diagnosis_group"] not in DIAGNOSES:
        raise ValueError("Unknown department or diagnosis group")
    if row["age_band"] not in ("18-39", "40-59", "60-79", "80+"):
        raise ValueError("Unknown age band")
    if not 1 <= int(row["length_of_stay_days"]) <= 30:
        raise ValueError("Invalid length of stay")
    if not 0 <= int(row["prior_visits_12m"]) <= 12:
        raise ValueError("Invalid prior visits")
    if not 1 <= int(row["discharge_month"]) <= 12:
        raise ValueError("Invalid month")
    if int(row["readmitted_30d"]) not in (0, 1):
        raise ValueError("Invalid readmission value")


def analyze(data_path: Path, output_dir: Path) -> dict[str, int | float]:
    with data_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != list(FIELDS):
            raise ValueError("Unexpected input schema")
        rows = list(reader)
    if not rows:
        raise ValueError("No encounters found")
    ids = set()
    for row in rows:
        validate(row)
        if not row["encounter_id"].startswith("SYN-ENC-") or row["encounter_id"] in ids:
            raise ValueError("Only unique synthetic encounter IDs are accepted")
        ids.add(row["encounter_id"])

    connection = sqlite3.connect(":memory:")
    connection.execute(
        "CREATE TABLE encounters (encounter_id TEXT PRIMARY KEY, department TEXT, age_band TEXT, "
        "diagnosis_group TEXT, length_of_stay_days INTEGER, prior_visits_12m INTEGER, "
        "discharge_month INTEGER, readmitted_30d INTEGER)"
    )
    connection.executemany(
        "INSERT INTO encounters VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [tuple(row[field] for field in FIELDS) for row in rows],
    )
    # Segments are descriptive rules, not a clinically validated risk model.
    connection.execute(
        "CREATE VIEW segmented AS SELECT *, CASE "
        "WHEN prior_visits_12m >= 4 OR length_of_stay_days >= 10 THEN 'High' "
        "WHEN prior_visits_12m >= 2 OR length_of_stay_days >= 5 THEN 'Medium' "
        "ELSE 'Low' END AS risk_segment FROM encounters"
    )
    department_rows = connection.execute(
        "SELECT department, COUNT(*) AS encounters, SUM(readmitted_30d) AS readmissions, "
        "ROUND(100.0 * AVG(readmitted_30d), 2) AS readmission_rate_pct "
        "FROM segmented GROUP BY department ORDER BY readmission_rate_pct DESC"
    ).fetchall()
    segment_rows = connection.execute(
        "SELECT risk_segment, COUNT(*) AS encounters, SUM(readmitted_30d) AS readmissions, "
        "ROUND(100.0 * AVG(readmitted_30d), 2) AS readmission_rate_pct "
        "FROM segmented GROUP BY risk_segment "
        "ORDER BY CASE risk_segment WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END"
    ).fetchall()
    monthly_rows = connection.execute(
        "SELECT discharge_month, COUNT(*) AS encounters, "
        "ROUND(100.0 * AVG(readmitted_30d), 2) AS readmission_rate_pct "
        "FROM segmented GROUP BY discharge_month ORDER BY discharge_month"
    ).fetchall()
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, columns, values in (
        ("department_summary.csv", ("department", "encounters", "readmissions", "readmission_rate_pct"), department_rows),
        ("risk_segments.csv", ("risk_segment", "encounters", "readmissions", "readmission_rate_pct"), segment_rows),
        ("monthly_trends.csv", ("discharge_month", "encounters", "readmission_rate_pct"), monthly_rows),
    ):
        with (output_dir / name).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(columns)
            writer.writerows(values)

    total = len(rows)
    readmissions = sum(int(row["readmitted_30d"]) for row in rows)
    bars = "".join(
        f'<div class="bar-row"><span>{html.escape(department)}</span>'
        f'<div class="track"><div class="fill" style="width:{rate}%"></div></div>'
        f'<strong>{rate:.1f}%</strong></div>'
        for department, _, _, rate in department_rows
    )
    report = f"""<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Readmission analysis demo</title><style>
body{{font:16px/1.5 system-ui,sans-serif;background:#0c1424;color:#e7f2ff;max-width:900px;margin:0 auto;padding:40px 24px}}
h1{{font-size:clamp(2rem,6vw,3.5rem);line-height:1.05}}.note{{color:#99aec9}}.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:16px;margin:32px 0}}
.card{{background:#17253b;border:1px solid #324762;border-radius:16px;padding:22px}}.card strong{{display:block;font-size:2rem;color:#62dfdf}}
.bar-row{{display:grid;grid-template-columns:155px 1fr 65px;gap:15px;align-items:center;margin:16px 0}}.track{{background:#27364e;border-radius:30px;height:18px;overflow:hidden}}.fill{{height:100%;background:linear-gradient(90deg,#34d8c9,#719aff)}}
@media(max-width:550px){{.bar-row{{grid-template-columns:1fr 1fr;gap:6px}}.track{{grid-column:1/-1;grid-row:2}}}}
</style><main><p class="note">SYNTHETIC DATA · REPRODUCIBLE SQL ANALYSIS</p><h1>Patient readmission patterns</h1><p>Demonstration only. Not a clinical model or decision aid.</p>
<div class="cards"><div class="card">Encounters<strong>{total:,}</strong></div><div class="card">30-day readmissions<strong>{readmissions:,}</strong></div><div class="card">Observed rate<strong>{100 * readmissions / total:.1f}%</strong></div></div>
<h2>Rate by department</h2>{bars}<p class="note">Generated records have no patient identifiers. Department differences are artifacts of the synthetic generator, not medical findings.</p></main></html>"""
    (output_dir / "dashboard.html").write_text(report, encoding="utf-8")
    connection.close()
    return {"encounters": total, "readmissions": readmissions, "readmission_rate_pct": round(100 * readmissions / total, 2)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("outputs/synthetic_encounters.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--rows", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if not args.data.exists():
        write_csv(args.data, args.rows, args.seed)
    print(analyze(args.data, args.output_dir))
