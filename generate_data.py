"""Generate non-identifiable, deterministic hospital encounter data."""

from __future__ import annotations

import argparse
import csv
import math
import random
from pathlib import Path

FIELDS = (
    "encounter_id",
    "department",
    "age_band",
    "diagnosis_group",
    "length_of_stay_days",
    "prior_visits_12m",
    "discharge_month",
    "readmitted_30d",
)
DEPARTMENTS = ("Cardiology", "Endocrinology", "General Medicine", "Pulmonology", "Surgery")
DIAGNOSES = ("Cardiovascular", "Diabetes", "Infection", "Respiratory", "Other")


def make_rows(count: int = 10000, seed: int = 42) -> list[dict[str, int | str]]:
    if count < 10:
        raise ValueError("count must be at least 10")
    rng = random.Random(seed)
    rows = []
    for index in range(count):
        department = rng.choice(DEPARTMENTS)
        diagnosis = rng.choice(DIAGNOSES)
        age_band = rng.choice(("18-39", "40-59", "60-79", "80+"))
        stay = min(30, max(1, round(rng.gammavariate(2.0, 2.2))))
        visits = min(12, int(rng.expovariate(0.55)))
        log_odds = (
            -3.0
            + 0.095 * stay
            + 0.29 * visits
            + (0.35 if age_band in ("60-79", "80+") else 0)
            + (0.35 if diagnosis in ("Cardiovascular", "Diabetes") else 0)
        )
        chance = 1 / (1 + math.exp(-log_odds))
        rows.append(
            {
                "encounter_id": f"SYN-ENC-{index + 1:07d}",
                "department": department,
                "age_band": age_band,
                "diagnosis_group": diagnosis,
                "length_of_stay_days": stay,
                "prior_visits_12m": visits,
                "discharge_month": rng.randint(1, 12),
                "readmitted_30d": int(rng.random() < chance),
            }
        )
    return rows


def write_csv(path: Path, count: int = 10000, seed: int = 42) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(make_rows(count, seed))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("outputs/synthetic_encounters.csv"))
    parser.add_argument("--rows", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    write_csv(args.output, args.rows, args.seed)
    print(f"Wrote {args.rows:,} synthetic encounters to {args.output}")
