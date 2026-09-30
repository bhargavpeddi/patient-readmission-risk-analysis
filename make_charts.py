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


INK, MUTED, GRID, SURFACE = "#1f2328", "#6b7280", "#e5e7eb", "#fcfcfb"
BLUE, ORANGE = "#2a78d6", "#eb6834"


def style(ax) -> None:
    ax.set_facecolor(SURFACE)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(GRID)
    ax.tick_params(colors=MUTED)


def department_chart(output_dir: Path, docs_dir: Path) -> None:
    """Readmission rate by department against the overall rate."""
    rows = sorted(read(output_dir / "department_summary.csv"), key=lambda r: float(r["readmission_rate_pct"]))
    total_enc = sum(int(r["encounters"]) for r in rows)
    overall = 100 * sum(int(r["readmissions"]) for r in rows) / total_enc

    fig, ax = plt.subplots(figsize=(10, 5.5), facecolor=SURFACE)
    style(ax)
    names = [r["department"] for r in rows]
    rates = [float(r["readmission_rate_pct"]) for r in rows]
    ax.barh(names, rates, color=BLUE, height=0.6)
    for y, (rate, row) in enumerate(zip(rates, rows)):
        ax.text(max(rates) * 1.06, y, f"{rate:.1f}%  ({int(row['readmissions']):,} of {int(row['encounters']):,})",
                va="center", color=INK, fontsize=10)
    ax.axvline(overall, color=MUTED, linestyle="--", linewidth=1.5)
    ax.text(overall, -0.62, f" overall {overall:.1f}%", color=MUTED, fontsize=10, va="center")
    ax.set_ylim(-0.85, len(rows) - 0.5)
    ax.set_xlim(0, max(rates) * 1.6)
    ax.set_xlabel("30-day readmission rate (%)", color=INK)
    ax.set_title("30-day readmission rate by department", loc="left", fontweight="bold", color=INK)
    ax.tick_params(axis="y", colors=INK, length=0)
    ax.grid(axis="x", alpha=0.6, color=GRID)
    fig.tight_layout()
    fig.savefig(docs_dir / "department_rates.png", dpi=200)


def segment_volume_chart(output_dir: Path, docs_dir: Path) -> None:
    """Encounters per risk segment, split into readmitted vs not."""
    rows = read(output_dir / "risk_segments.csv")
    names = [r["risk_segment"] for r in rows]
    readm = [int(r["readmissions"]) for r in rows]
    rest = [int(r["encounters"]) - n for r, n in zip(rows, readm)]

    fig, ax = plt.subplots(figsize=(10, 5.5), facecolor=SURFACE)
    style(ax)
    ax.bar(names, rest, color=BLUE, width=0.55, label="Not readmitted", edgecolor=SURFACE, linewidth=2)
    ax.bar(names, readm, bottom=rest, color=ORANGE, width=0.55, label="Readmitted within 30 days", edgecolor=SURFACE, linewidth=2)
    for x, (row, n, r) in enumerate(zip(rows, readm, rest)):
        ax.text(x, n + r + 60, f"{int(row['encounters']):,} encounters\n{float(row['readmission_rate_pct']):.1f}% readmitted",
                ha="center", va="bottom", color=INK, fontsize=10)
    ax.set_ylim(0, max(int(r["encounters"]) for r in rows) * 1.25)
    ax.set_ylabel("Encounters", color=INK)
    ax.set_title("Encounters and readmissions by risk segment", loc="left", fontweight="bold", color=INK)
    ax.tick_params(axis="x", colors=INK, length=0)
    ax.grid(axis="y", alpha=0.6, color=GRID)
    ax.legend(frameon=False, loc="upper left")
    fig.tight_layout()
    fig.savefig(docs_dir / "segment_volume.png", dpi=200)


if __name__ == "__main__":
    main()
    department_chart(Path("outputs"), Path("docs"))
    segment_volume_chart(Path("outputs"), Path("docs"))
    print("Wrote docs/department_rates.png and docs/segment_volume.png")
