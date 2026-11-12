import datetime

import pytest
from conftest import HEADER, row, write_month

from jobmarket.database import build_database


def values(con, sql):
    return [r[0] if len(r) == 1 else r for r in con.sql(sql).fetchall()]


def salary(con, posting_id):
    return con.sql(
        f"select annual_salary from postings where posting_id = '{posting_id}'"
    ).fetchall()[0][0]


def test_loads_every_month_and_tags_the_source_month(month_files):
    con = build_database(month_files)
    assert values(con, "select count(*) from postings") == [9]
    assert values(con, "select distinct source_month from postings order by 1") == [
        datetime.date(2025, 11, 1),
        datetime.date(2026, 10, 1),
    ]


def test_columns_added_in_newer_months_are_null_in_older_ones(month_files):
    con = build_database(month_files)
    language = dict(
        con.sql(
            'select "WIC Job Location Snapshot ID", "Official Language" from raw_postings '
            """where "WIC Job Location Snapshot ID" in ('1', '9')"""
        ).fetchall()
    )
    assert language == {"1": "English", "9": None}


def test_double_space_header_is_normalized(month_files):
    con = build_database(month_files)
    assert values(con, "select economic_region from postings where posting_id = '1'") == [
        "Toronto Region"
    ]


@pytest.mark.parametrize(
    ("posting_id", "expected"),
    [
        ("1", 30 * 37.5 * 52),  # hourly, with weekly hours from the posting
        ("2", 20 * 40 * 52),  # hourly, hours missing: assume 40 per week
        ("3", 100_000),  # yearly range: midpoint
        ("4", 5000 * 12),
        ("6", 200 * 260),
        ("7", 1000 * 52),
        ("8", 2000 * 26),
    ],
)
def test_salaries_are_annualized(month_files, posting_id, expected):
    assert salary(build_database(month_files), posting_id) == pytest.approx(expected)


def test_missing_salary_stays_null(month_files):
    assert salary(build_database(month_files), "5") is None


def test_tech_and_toronto_flags(month_files):
    con = build_database(month_files)
    flags = dict(
        (r[0], r[1:])
        for r in con.sql(
            "select posting_id, is_tech, occupation_family, is_toronto from postings"
        ).fetchall()
    )
    assert flags["1"] == (True, "Software", True)
    assert flags["2"] == (False, None, False)  # retail, Ottawa
    assert flags["3"] == (True, "Data", True)
    assert flags["9"] == (False, None, True)  # 21200 is architects, not tech


def test_types_and_na_handling(month_files):
    con = build_database(month_files)
    first = con.sql(
        "select first_posting_date, vacancies, education, is_external from postings "
        "where posting_id = '8'"
    ).fetchall()[0]
    assert first == (datetime.date(2026, 10, 2), 1, None, True)


def test_writes_a_database_file(month_files, tmp_path):
    path = tmp_path / "jobs.duckdb"
    build_database(month_files, path).close()
    assert path.exists()


def test_rejects_badly_named_files(tmp_path):
    path = write_month(tmp_path / "october.csv", [row("1")])
    with pytest.raises(ValueError, match="YYYY-MM"):
        build_database([path])


def test_rejects_files_missing_required_columns(tmp_path):
    path = tmp_path / "2026-10.csv"
    header = [column for column in HEADER if column != "Salary Per"]
    path.write_text("\t".join(header) + "\n", encoding="utf-16")
    with pytest.raises(ValueError, match="Salary Per"):
        build_database([path])


def test_requires_at_least_one_file():
    with pytest.raises(ValueError, match="No raw files"):
        build_database([])
