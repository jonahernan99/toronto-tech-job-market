import pytest
from conftest import row, write_month

from jobmarket.analysis import load_queries, run_analysis
from jobmarket.database import build_database


@pytest.fixture
def con(tmp_path):
    rows = [
        # The same software ad in Toronto and Mississauga (both Toronto Region) and Ottawa.
        row("1", city="Toronto"),
        row("2", city="Mississauga"),
        row("3", city="Ottawa", region="Ottawa Region"),
        # A data scientist in Toronto at $100,000 a year.
        row("4", noc="21211", per="Year", low="100000", high="100000"),
        # A software ad with a yearly salary entered as $25: implausible.
        row("5", per="Year", low="25", high="25"),
        # Not tech.
        row("6", noc="64100"),
    ]
    return build_database([write_month(tmp_path / "2026-10.csv", rows)])


def by_name(tables):
    return {table.name: table for table in tables}


def as_dicts(table):
    return [dict(zip(table.columns, values, strict=True)) for values in table.rows]


def test_every_query_has_a_title_and_notes():
    queries = load_queries()
    assert [q.name[:2] for q in queries] == ["01", "02", "03", "04", "05", "06", "07", "08"]
    for query in queries:
        assert query.title and query.title != query.name
        assert query.notes


def test_overview_counts_rows_and_distinct_postings(con):
    (overview,) = as_dicts(by_name(run_analysis(con))["01_overview"])
    assert overview == {
        "months": 1,
        "rows": 6,
        "postings": 4,  # rows 1-3 are one ad
        "tech_rows": 5,
        "tech_postings": 3,
        "toronto_tech_rows": 4,
        "toronto_tech_postings": 3,
    }


def test_toronto_share_by_family(con):
    software = next(
        r
        for r in as_dicts(by_name(run_analysis(con))["02_toronto_share_by_family"])
        if r["family"] == "Software"
    )
    assert software == {
        "family": "Software",
        "canada_postings": 2,
        "toronto_postings": 2,
        "toronto_share_pct": 100.0,
    }


def test_salary_medians_skip_implausible_salaries_and_repeated_ads(con):
    salaries = {r["family"]: r for r in as_dicts(by_name(run_analysis(con))["03_salary_by_family"])}
    # Software in Toronto: the repeated ad counts once (30 $/h x 37.5 h x 52 = 58,500);
    # the $25 "yearly" salary is excluded.
    assert salaries["Software"]["toronto_postings"] == 1
    assert salaries["Software"]["toronto_median"] == 58500
    assert salaries["Software"]["rest_postings"] == 1  # the Ottawa copy
    assert salaries["Data"]["toronto_median"] == 100000


def test_salary_quality_counts_implausible_rows(con):
    quality = {r["pay_unit"]: r for r in as_dicts(by_name(run_analysis(con))["08_salary_quality"])}
    assert quality["Year"]["implausible"] == 1
    assert quality["Hour"]["implausible"] == 0


def test_all_queries_run_on_the_fixture(month_files):
    tables = run_analysis(build_database(month_files))
    assert len(tables) == 8
    assert all(table.columns for table in tables)
