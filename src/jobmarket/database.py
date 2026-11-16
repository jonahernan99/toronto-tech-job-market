"""Load monthly Job Bank files into DuckDB and expose a clean ``postings`` view."""

from __future__ import annotations

import re
from collections.abc import Sequence
from importlib import resources
from pathlib import Path

import duckdb

from jobmarket.occupations import TECH_OCCUPATIONS

#: Raw columns the staging view needs, after collapsing repeated whitespace
#: (the source spells one of them "Economic  Region", with two spaces).
REQUIRED_COLUMNS = (
    "WIC Job Location Snapshot ID",
    "Job Title",
    "NOC21 Code",
    "NOC21 Code Name",
    "External Indicator",
    "First Posting Date",
    "Vacancy Count",
    "Education LOS",
    "Experience Level",
    "NAICS",
    "Province/Territory",
    "City",
    "Economic Region",
    "Employment Type",
    "Employment Term",
    "Salary Per",
    "Salary Minimum",
    "Salary Maximum",
    "Hours Per",
    "Hours Minimum",
    "Hours Maximum",
)

_MONTH_FILE_RE = re.compile(r"^\d{4}-\d{2}\.csv$")


def _quote(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def build_database(
    raw_files: Sequence[str | Path], database: str | Path = ":memory:"
) -> duckdb.DuckDBPyConnection:
    """Load ``YYYY-MM.csv`` files into DuckDB and create the ``postings`` view.

    The files are UTF-16, tab-separated, and their columns change between
    months, so they are combined by column name rather than by position.
    """
    paths = [Path(path) for path in raw_files]
    if not paths:
        raise ValueError("No raw files given")
    badly_named = [path.name for path in paths if not _MONTH_FILE_RE.match(path.name)]
    if badly_named:
        raise ValueError(f"Raw files must be named YYYY-MM.csv: {', '.join(badly_named)}")

    con = duckdb.connect(str(database))
    con.execute(
        """
        create or replace temp table raw_import as
        select * from read_csv(
            ?, encoding = 'utf-16', delim = '\t', header = true, all_varchar = true,
            union_by_name = true, filename = 'source_file'
        )
        """,
        [[str(path) for path in paths]],
    )

    columns = con.sql("select * from raw_import limit 0").columns
    renamed = {" ".join(column.split()): column for column in columns}
    missing = [column for column in REQUIRED_COLUMNS if column not in renamed]
    if missing:
        raise ValueError(f"Raw files are missing columns: {', '.join(missing)}")

    select_list = ", ".join(f"{_quote(old)} as {_quote(new)}" for new, old in renamed.items())
    con.execute(f"create or replace table raw_postings as select {select_list} from raw_import")
    con.execute("drop table raw_import")

    con.execute(
        "create or replace table occupations "
        "(noc_code varchar primary key, noc_name varchar, family varchar)"
    )
    con.executemany(
        "insert into occupations values (?, ?, ?)",
        [(code, name, family) for code, (name, family) in TECH_OCCUPATIONS.items()],
    )

    apply_staging(con)
    return con


def apply_staging(con: duckdb.DuckDBPyConnection) -> None:
    """(Re)create the ``postings`` view, so databases built earlier pick up new columns."""
    staging = resources.files("jobmarket").joinpath("sql/staging.sql").read_text("utf-8")
    con.execute(staging)
