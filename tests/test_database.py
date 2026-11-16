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


def build_one_month(tmp_path, rows):
    return build_database([write_month(tmp_path / "2026-10.csv", rows)])


def plausibility(con):
    return dict(con.sql("select posting_id, salary_is_plausible from postings").fetchall())


def test_salary_plausibility_catches_swapped_units(tmp_path):
    con = build_one_month(
        tmp_path,
        [
            row("ok"),  # 30 $/h
            row("hourly-as-yearly", per="Year", low="25", high="25"),  # $25 a year
            row("yearly-as-hourly", per="Hour", low="95000", high="95000"),
            row("missing", per="NA", low="NA", high="NA"),
        ],
    )
    assert plausibility(con) == {
        "ok": True,
        "hourly-as-yearly": False,
        "yearly-as-hourly": False,
        "missing": None,
    }


@pytest.mark.parametrize(
    ("rate", "plausible"), [("11.99", False), ("12", True), ("250", True), ("250.5", False)]
)
def test_salary_plausibility_bounds(tmp_path, rate, plausible):
    con = build_one_month(
        tmp_path, [row("1", low=rate, high=rate, hours_per="NA", hours_low="NA", hours_high="NA")]
    )
    assert plausibility(con) == {"1": plausible}


def test_implied_hourly_uses_posted_weekly_hours(tmp_path):
    con = build_one_month(tmp_path, [row("1", per="Year", low="78000", high="78000")])  # 37.5 h
    assert con.sql("select implied_hourly from postings").fetchall()[0][0] == pytest.approx(40.0)


def test_same_ad_in_two_cities_shares_a_posting_key(tmp_path):
    con = build_one_month(
        tmp_path,
        [
            row("toronto", city="Toronto"),
            row("mississauga", city="Mississauga"),
            row("different-pay", city="Toronto", low="31", high="31"),
        ],
    )
    keys = dict(con.sql("select posting_id, posting_key from postings").fetchall())
    assert keys["toronto"] == keys["mississauga"]
    assert keys["toronto"] != keys["different-pay"]
    assert con.sql("select count(distinct posting_key) from postings").fetchall()[0][0] == 2
