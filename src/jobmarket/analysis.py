"""Run the SQL analysis queries in ``sql/analysis`` against the ``postings`` view.

Each query lives in its own ``.sql`` file so it can be read and run on its own
in any DuckDB client. The first comment line holds the title
(``-- Title: ...``) and the following comment lines describe the method.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import resources

import duckdb


@dataclass(frozen=True)
class Table:
    """The result of one analysis query."""

    name: str
    title: str
    notes: str
    columns: tuple[str, ...]
    rows: list[tuple]


@dataclass(frozen=True)
class Query:
    name: str
    title: str
    notes: str
    sql: str


def _parse(name: str, sql: str) -> Query:
    title, notes = name, []
    for line in sql.splitlines():
        if not line.startswith("--"):
            break
        text = line.removeprefix("--").strip()
        if text.startswith("Title:"):
            title = text.removeprefix("Title:").strip()
        elif text:
            notes.append(text)
    return Query(name=name, title=title, notes=" ".join(notes), sql=sql)


def load_queries() -> list[Query]:
    """Load the bundled analysis queries in file-name order."""
    folder = resources.files("jobmarket").joinpath("sql/analysis")
    files = sorted(
        (entry for entry in folder.iterdir() if entry.name.endswith(".sql")),
        key=lambda entry: entry.name,
    )
    return [_parse(entry.name.removesuffix(".sql"), entry.read_text("utf-8")) for entry in files]


def run_analysis(con: duckdb.DuckDBPyConnection) -> list[Table]:
    """Run every analysis query and return the results in order."""
    tables = []
    for query in load_queries():
        relation = con.sql(query.sql)
        tables.append(
            Table(
                name=query.name,
                title=query.title,
                notes=query.notes,
                columns=tuple(relation.columns),
                rows=relation.fetchall(),
            )
        )
    return tables
