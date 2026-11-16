"""Render analysis results as a Markdown report."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date

from jobmarket.analysis import Table

ATTRIBUTION = (
    "Contains information licensed under the "
    "[Open Government Licence – Canada](https://open.canada.ca/en/open-government-licence-canada). "
    "Source: [Job Postings Advertised on Canada's National Job Bank Website]"
    "(https://open.canada.ca/data/en/dataset/ea639e28-c0fc-48bf-b5dd-b8899bd43072), "
    "Employment and Social Development Canada."
)


def _cell(value: object, column: str) -> str:
    if value is None:
        return "–"
    if isinstance(value, float):
        if column.endswith("_pct") or column == "pct":
            return f"{value:.1f}%"
        if value.is_integer():
            return f"{int(value):,}"
        return f"{value:,.2f}"
    if isinstance(value, int) and not isinstance(value, bool):
        return f"{value:,}"
    return str(value).replace("|", "\\|")


def _header(column: str) -> str:
    return column.replace("_pct", " %").replace("_", " ").capitalize()


def render_table(table: Table) -> str:
    lines = [f"## {table.title}", ""]
    if table.notes:
        lines += [f"_{table.notes}_", ""]
    if not table.rows:
        return "\n".join([*lines, "No rows."])
    lines.append("| " + " | ".join(_header(c) for c in table.columns) + " |")
    lines.append(
        "| "
        + " | ".join(
            "---:" if isinstance(value, int | float) and not isinstance(value, bool) else "---"
            for value in table.rows[0]
        )
        + " |"
    )
    for values in table.rows:
        cells = (_cell(v, c) for v, c in zip(values, table.columns, strict=True))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def render_report(tables: Sequence[Table], *, generated: date | None = None) -> str:
    """Render every table, with the data attribution the licence requires."""
    generated = generated or date.today()
    parts = [
        "# Toronto Tech Job Market: SQL Analysis Report",
        "",
        f"Generated on {generated.isoformat()} by `jobmarket report` from the queries in "
        "[`src/jobmarket/sql/analysis`](../src/jobmarket/sql/analysis). Salaries are in CAD.",
        "",
    ]
    for table in tables:
        parts += [render_table(table), ""]
    parts += ["---", "", ATTRIBUTION, ""]
    return "\n".join(parts)
