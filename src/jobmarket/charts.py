"""Static PNG charts for the Markdown report.

Each chart is drawn from an analysis table, so the numbers on the chart and in
the table beside it always agree. Styling follows a validated categorical
palette (blue for the Toronto Region, orange for the comparison series),
hairline grids, one value axis per chart, and a legend plus direct labels so
identity never depends on color alone. Requires the ``charts`` extra.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from jobmarket.analysis import Table

TORONTO = "#2a78d6"  # categorical slot 1
COMPARISON = "#eb6834"  # categorical slot 2
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"


def _rows(table: Table) -> list[dict]:
    return [dict(zip(table.columns, values, strict=True)) for values in table.rows]


def _style(ax, *, value_axis: str) -> None:
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(AXIS)
    ax.tick_params(colors=INK_SECONDARY, labelsize=9, length=0)
    ax.grid(axis=value_axis, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def _finish(fig, ax, title: str, subtitle: str, path: Path) -> Path:
    ax.set_title(title, loc="left", color=INK, fontsize=12, fontweight="bold", pad=24)
    ax.text(0, 1.02, subtitle, transform=ax.transAxes, color=INK_SECONDARY, fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=150, facecolor=SURFACE)
    return path


def salary_by_family(table: Table, path: Path) -> Path:
    import matplotlib.pyplot as plt

    rows = sorted(_rows(table), key=lambda r: r["toronto_median"] or 0)
    families = [r["family"] for r in rows]
    toronto = [(r["toronto_median"] or 0) / 1000 for r in rows]
    rest = [(r["rest_of_canada_median"] or 0) / 1000 for r in rows]
    positions = range(len(rows))
    height = 0.36

    fig, ax = plt.subplots(figsize=(8, 4.6), facecolor=SURFACE)
    _style(ax, value_axis="x")
    bars_t = ax.barh(
        [p + height / 2 + 0.02 for p in positions],
        toronto,
        height,
        color=TORONTO,
        label="Toronto Region",
    )
    bars_r = ax.barh(
        [p - height / 2 - 0.02 for p in positions],
        rest,
        height,
        color=COMPARISON,
        label="Rest of Canada",
    )
    for bars in (bars_t, bars_r):
        ax.bar_label(
            bars,
            labels=[f"${b.get_width():.0f}k" for b in bars],
            padding=4,
            color=INK_SECONDARY,
            fontsize=8,
        )
    ax.set_yticks(list(positions), families, color=INK)
    ax.set_xlabel("Median annual salary (CAD, thousands)", color=MUTED, fontsize=9)
    ax.set_xlim(0, max(toronto + rest) * 1.15)
    ax.legend(loc="lower right", frameon=False, fontsize=9, labelcolor=INK_SECONDARY)
    return _finish(
        fig,
        ax,
        "Advertised salaries are higher in Toronto",
        "All postings, including external job boards' repeated ranges; median per posting",
        path,
    )


def monthly_trend(table: Table, path: Path) -> Path:
    import matplotlib.pyplot as plt

    rows = _rows(table)
    months = [r["month"] for r in rows]
    fig, ax = plt.subplots(figsize=(8, 4), facecolor=SURFACE)
    _style(ax, value_axis="y")
    for column, color, label in (
        ("canada_postings", COMPARISON, "Canada"),
        ("toronto_postings", TORONTO, "Toronto Region"),
    ):
        values = [r[column] for r in rows]
        ax.plot(months, values, color=color, linewidth=2, marker="o", markersize=5, label=label)
        ax.annotate(
            f"{label}: {values[-1]:,}",
            (len(months) - 1, values[-1]),
            xytext=(6, 0),
            textcoords="offset points",
            va="center",
            color=INK_SECONDARY,
            fontsize=8,
        )
    ax.set_ylim(0, max(r["canada_postings"] for r in rows) * 1.15)
    ax.set_ylabel("Distinct tech postings", color=MUTED, fontsize=9)
    ax.set_xlim(-0.5, len(months) + 1.5)
    ax.tick_params(axis="x", rotation=45)
    ax.legend(loc="lower left", frameon=False, fontsize=9, labelcolor=INK_SECONDARY)
    return _finish(
        fig,
        ax,
        "Monthly tech postings on Job Bank",
        "Toronto Region vs. all of Canada, distinct postings per monthly file",
        path,
    )


def education(table: Table, path: Path) -> Path:
    import matplotlib.pyplot as plt

    rows = list(reversed(_rows(table)))  # barh draws upwards: lowest level ends up on top
    fig, ax = plt.subplots(figsize=(8, 0.42 * len(rows) + 1.6), facecolor=SURFACE)
    _style(ax, value_axis="x")
    bars = ax.barh([r["education"] for r in rows], [r["pct"] for r in rows], 0.6, color=TORONTO)
    ax.bar_label(
        bars, labels=[f"{r['pct']:.0f}%" for r in rows], padding=4, color=INK_SECONDARY, fontsize=8
    )
    ax.tick_params(axis="y", colors=INK)
    ax.set_xlabel(
        "Share of Toronto Region tech postings stating education (%)", color=MUTED, fontsize=9
    )
    ax.set_xlim(0, max(r["pct"] for r in rows) * 1.15)
    return _finish(
        fig,
        ax,
        "Education asked for in Toronto tech postings",
        "Direct employer postings only, ordered from lowest to highest level",
        path,
    )


def salary_by_experience(table: Table, path: Path) -> Path:
    import matplotlib.pyplot as plt

    rows = list(reversed(_rows(table)))  # least experience ends up on top
    positions = range(len(rows))
    fig, ax = plt.subplots(figsize=(8, 0.5 * len(rows) + 1.6), facecolor=SURFACE)
    _style(ax, value_axis="x")
    for y, r in zip(positions, rows, strict=True):
        ax.plot(
            [r["p25"] / 1000, r["p75"] / 1000],
            [y, y],
            color=TORONTO,
            linewidth=6,
            alpha=0.3,
            solid_capstyle="round",
        )
        ax.plot(r["median"] / 1000, y, "o", color=TORONTO, markersize=8)
        ax.annotate(
            f"${r['median'] / 1000:.0f}k",
            (r["p75"] / 1000, y),
            xytext=(8, 0),
            textcoords="offset points",
            va="center",
            color=INK_SECONDARY,
            fontsize=8,
        )
    ax.set_yticks(list(positions), [r["experience"] for r in rows], color=INK)
    ax.set_xlabel(
        "Annual salary (CAD, thousands): dot = median, bar = middle half of postings",
        color=MUTED,
        fontsize=9,
    )
    ax.set_xlim(
        min(r["p25"] for r in rows) / 1000 * 0.85, max(r["p75"] for r in rows) / 1000 * 1.12
    )
    return _finish(
        fig,
        ax,
        "Pay rises with the experience asked for",
        "Toronto Region tech postings published directly by employers",
        path,
    )


#: Analysis table name -> (chart function, file name)
CHARTS = {
    "03_salary_by_family": (salary_by_family, "salary_by_family.png"),
    "05_monthly_trend": (monthly_trend, "monthly_trend.png"),
    "06_toronto_education": (education, "education.png"),
    "09_toronto_salary_by_experience": (salary_by_experience, "salary_by_experience.png"),
}


def render_charts(tables: Sequence[Table], out_dir: str | Path) -> dict[str, Path]:
    """Draw every chart whose table is present and has rows; return name -> file."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written = {}
    for table in tables:
        if table.name not in CHARTS or not table.rows:
            continue
        draw, filename = CHARTS[table.name]
        written[table.name] = draw(table, out_dir / filename)
        plt.close("all")
    return written
