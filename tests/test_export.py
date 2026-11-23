import csv

import pytest
from conftest import row, write_month

from jobmarket.cli import EXIT_ERROR, EXIT_OK, main
from jobmarket.database import build_database
from jobmarket.export import COLUMNS, export_postings


@pytest.fixture
def month_file(tmp_path):
    rows = [
        # The same software ad in Toronto and Mississauga (both Toronto Region) and Ottawa.
        row("1", city="Toronto"),
        row("2", city="Mississauga"),
        row("3", city="Ottawa", region="Ottawa Region"),
        # A data scientist on an external board at $100,000 a year, asking for a degree.
        row(
            "4",
            noc="21211",
            per="Year",
            low="100000",
            high="100000",
            external="1",
            education="Bachelor's degree",
            experience="1 year to less than 2 years",
        ),
        # A software ad with a yearly salary entered as $25: implausible.
        row("5", per="Year", low="25", high="25"),
        # Not tech.
        row("6", noc="64100"),
    ]
    (tmp_path / "raw").mkdir()
    return write_month(tmp_path / "raw" / "2026-10.csv", rows)


def read(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_export_has_one_row_per_posting_and_region(month_file, tmp_path):
    con = build_database([month_file])
    out = tmp_path / "out" / "postings.csv"
    assert export_postings(con, out) == 4

    rows = read(out)
    assert tuple(rows[0]) == COLUMNS
    assert sorted((r["region"], r["noc_code"], r["annual_salary"]) for r in rows) == [
        ("Rest of Canada", "21232", "58500"),
        ("Toronto Region", "21211", "100000"),
        ("Toronto Region", "21232", ""),
        ("Toronto Region", "21232", "58500"),
    ]


def test_export_carries_labels_and_levels(month_file, tmp_path):
    con = build_database([month_file])
    out = tmp_path / "postings.csv"
    export_postings(con, out)

    scientist = next(r for r in read(out) if r["noc_code"] == "21211")
    assert scientist.pop("posting").isdigit()
    assert scientist == {
        "month": "2026-10",
        "region": "Toronto Region",
        "economic_region": "Toronto Region",
        "family": "Data",
        "noc_code": "21211",
        "occupation": "Some occupation",
        "source": "External job board",
        "experience": "1 to 2 years",
        "experience_rank": "3",
        "education": "Bachelor's degree",
        "education_rank": "7",
        "annual_salary": "100000",
    }
    software = next(r for r in read(out) if r["region"] == "Rest of Canada")
    assert software["source"] == "Direct employer"
    assert software["experience"] == software["experience_rank"] == ""


def test_an_ad_in_two_regions_shares_its_posting_id(month_file, tmp_path):
    con = build_database([month_file])
    out = tmp_path / "postings.csv"
    export_postings(con, out)
    rows = read(out)

    # Rows 1 to 3 are one ad: Toronto and Mississauga merge, Ottawa stays apart.
    software = [r for r in rows if r["noc_code"] == "21232" and r["annual_salary"] == "58500"]
    assert sorted(r["economic_region"] for r in software) == ["Ottawa Region", "Toronto Region"]
    assert len({r["posting"] for r in software}) == 1
    assert len({r["posting"] for r in rows}) == 3


def test_export_is_deterministic(month_file, tmp_path):
    con = build_database([month_file])
    first, second = tmp_path / "a.csv", tmp_path / "b.csv"
    export_postings(con, first)
    export_postings(con, second)
    assert first.read_bytes() == second.read_bytes()
    assert b"\r\n" not in first.read_bytes()


def test_export_command(month_file, tmp_path, capsys):
    db = tmp_path / "jobs.duckdb"
    assert main(["build", "--raw", str(month_file.parent), "--db", str(db)]) == EXIT_OK
    out = tmp_path / "dashboard" / "postings.csv"
    assert main(["export", "--db", str(db), "--out", str(out)]) == EXIT_OK
    assert "Wrote 4 rows, one per tech posting and economic region" in capsys.readouterr().out
    assert len(read(out)) == 4


def test_export_without_database_is_an_error(tmp_path, capsys):
    assert main(["export", "--db", str(tmp_path / "missing.duckdb")]) == EXIT_ERROR
    assert "run `jobmarket build` first" in capsys.readouterr().err
