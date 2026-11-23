"""Export one row per tech posting, for the dashboard and for use in other tools.

There is one row per posting and economic region: an ad repeated in Toronto
and Mississauga is one Toronto Region row, and an ad listed in Ottawa and
Calgary is one row for each. ``posting`` identifies the ad, so counts for a
group of regions (such as the rest of Canada) must count distinct postings.
Salaries appear only when plausible. The extract holds no employer names or
free-text job titles, only the fields the dashboard needs.
"""

from __future__ import annotations

import csv
from pathlib import Path

import duckdb

COLUMNS: tuple[str, ...] = (
    "posting",
    "month",
    "region",
    "economic_region",
    "family",
    "noc_code",
    "occupation",
    "source",
    "experience",
    "experience_rank",
    "education",
    "education_rank",
    "annual_salary",
)

EXPORT_SQL = """
select
    dense_rank() over (order by posting_key) as posting,
    strftime(source_month, '%Y-%m') as month,
    case when is_toronto then 'Toronto Region' else 'Rest of Canada' end as region,
    economic_region,
    occupation_family as family,
    noc_code,
    noc_name as occupation,
    case when is_external then 'External job board' else 'Direct employer' end as source,
    experience_level as experience,
    experience_rank,
    education_level as education,
    education_rank,
    case when salary_is_plausible then cast(round(annual_salary) as integer) end
        as annual_salary
from postings
where is_tech
qualify row_number() over (partition by posting_key, economic_region order by posting_id) = 1
order by all
"""


def export_postings(con: duckdb.DuckDBPyConnection, path: Path) -> int:
    """Write the tech postings to ``path`` as CSV and return the number of rows.

    Rows are fully sorted, so exporting the same data twice gives the same file.
    Missing values are empty fields.
    """
    relation = con.sql(EXPORT_SQL)
    if tuple(relation.columns) != COLUMNS:
        raise ValueError(f"Unexpected export columns: {relation.columns}")
    rows = relation.fetchall()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(COLUMNS)
        writer.writerows(["" if value is None else value for value in row] for row in rows)
    return len(rows)
