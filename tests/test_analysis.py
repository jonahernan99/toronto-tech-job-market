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
    assert [q.name[:2] for q in queries] == [f"{i:02d}" for i in range(1, 12)]
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
    assert len(tables) == 11
    assert all(table.columns for table in tables)


def test_education_and_experience_tables_are_ordered_by_level(tmp_path):
    rows = [
        row("1", education="Bachelor's degree", experience="5 years or more"),
        row(
            "2",
            education="Secondary (high) school graduation certificate",
            low="31",
            high="31",
            experience="No experience",
        ),
        row(
            "3",
            education="Master's degree",
            low="32",
            high="32",
            experience="2 years to less than 3 years",
        ),
    ]
    tables = by_name(run_analysis(build_database([write_month(tmp_path / "2026-10.csv", rows)])))
    assert [r[0] for r in tables["06_toronto_education"].rows] == [
        "High school",
        "Bachelor's degree",
        "Master's degree",
    ]
    assert [r[0] for r in tables["07_toronto_experience"].rows] == [
        "None",
        "2 to 3 years",
        "5 years or more",
    ]


def test_salary_by_experience_uses_direct_postings_in_level_order(tmp_path):
    rows = [
        row("1", experience="5 years or more", low="60", high="60"),
        row("2", experience="No experience", low="30", high="30"),
        row("3", experience="No experience", low="32", high="32", title="junior developer"),
        # External postings do not report experience, so they are left out.
        row("4", external="1", low="90", high="90"),
    ]
    tables = by_name(run_analysis(build_database([write_month(tmp_path / "2026-10.csv", rows)])))
    experience = as_dicts(tables["09_toronto_salary_by_experience"])
    assert [r["experience"] for r in experience] == ["None", "5 years or more"]
    assert experience[0]["postings"] == 2
    assert experience[0]["median"] == 60500  # 31 $/h x 37.5 h x 52 = 60,450, rounded to $100
    assert experience[1]["median"] == 117000


def test_repeated_wide_ranges_are_counted_by_source(tmp_path):
    rows = []
    # 20 external postings sharing one wide range: a repeated template.
    rows += [
        row(f"w{i}", noc="21211", low="30", high="69.74", external="1", title=f"data scientist {i}")
        for i in range(20)
    ]
    # 19 postings sharing another wide range: below the threshold.
    rows += [
        row(f"n{i}", low="28", high="60", external="1", title=f"developer {i}") for i in range(19)
    ]
    # 20 postings at one round value: repeated, but not a wide range.
    rows += [row(f"r{i}", low="50", high="50", title=f"engineer {i}") for i in range(20)]
    tables = by_name(run_analysis(build_database([write_month(tmp_path / "2026-10.csv", rows)])))
    repeated = {r["source"]: r for r in as_dicts(tables["10_repeated_salary_ranges"])}
    assert repeated["External job boards"]["postings_with_salary"] == 39
    assert repeated["External job boards"]["in_repeated_ranges"] == 20
    assert repeated["Direct employer postings"]["in_repeated_ranges"] == 0
    assert repeated["All"] == {
        "source": "All",
        "postings_with_salary": 59,
        "in_repeated_ranges": 20,
        "repeated_pct": 33.9,
    }


def test_direct_salary_by_family_leaves_out_external_postings(tmp_path):
    rows = [
        row("1"),  # direct, Toronto: 58,500
        row("2", external="1", per="Year", low="150000", high="150000", title="lead developer"),
        row("3", region="Ottawa Region", city="Ottawa", low="40", high="40", title="developer"),
    ]
    tables = by_name(run_analysis(build_database([write_month(tmp_path / "2026-10.csv", rows)])))
    (software,) = as_dicts(tables["11_direct_salary_by_family"])
    assert software == {
        "family": "Software",
        "toronto_postings": 1,
        "toronto_median": 58500,
        "rest_postings": 1,
        "rest_of_canada_median": 78000,
    }
