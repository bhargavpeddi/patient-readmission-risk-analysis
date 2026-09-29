"""Plot readmission rates from the CSVs written by analyze.py. Requires matplotlib."""

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def main(output_dir: Path = Path("outputs"), docs_dir: Path = Path("docs")) -> None:
    segments = read(output_dir / "risk_segments.csv")
    months = read(output_dir / "monthly_trends.csv")
    docs_dir.mkdir(exist_ok=True)

    fig, (left, right) = plt.subplots(1, 2, figsize=(12, 5), gridspec_kw={"width_ratios": [1, 1.4]})
    names = [row["risk_segment"] for row in segments]
    rates = [float(row["readmission_rate_pct"]) for row in segments]
    bars = left.bar(names, rates, color=["#d9534f", "#f0ad4e", "#5cb85c"])
    for bar, rate in zip(bars, rates):
        left.text(bar.get_x() + bar.get_width() / 2, rate + 0.5, f"{rate:.1f}%", ha="center", fontweight="bold")
    left.set_title("30-day readmission rate by risk segment", loc="left", fontweight="bold")
    left.set_ylabel("Readmission rate (%)")
    left.set_ylim(0, max(rates) * 1.2)

    right.plot([int(r["discharge_month"]) for r in months], [float(r["readmission_rate_pct"]) for r in months],
               marker="o", color="#2f7fd8", linewidth=2)
    right.set_xticks(range(1, 13))
    right.set_title("Readmission rate by discharge month", loc="left", fontweight="bold")
    right.set_xlabel("Month")
    right.grid(alpha=0.3)
    for ax in (left, right):
        ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(docs_dir / "readmission_rates.png", dpi=120)
    print(f"Wrote {docs_dir / 'readmission_rates.png'}")


if __name__ == "__main__":
    main()
