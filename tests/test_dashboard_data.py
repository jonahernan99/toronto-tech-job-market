"""Checks on the committed extract that the dashboard reads."""

import csv
import re
from pathlib import Path

import pytest

from jobmarket.export import COLUMNS
from jobmarket.levels import EDUCATION_LEVELS, EXPERIENCE_LEVELS
from jobmarket.occupations import TECH_OCCUPATIONS

EXTRACT = Path(__file__).resolve().parents[1] / "dashboard" / "data" / "tech_postings.csv"


@pytest.fixture(scope="module")
def rows():
    with EXTRACT.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        assert tuple(reader.fieldnames) == COLUMNS
        return list(reader)


def test_extract_covers_twelve_months_and_both_regions(rows):
    months = {row["month"] for row in rows}
    assert all(re.fullmatch(r"\d{4}-\d{2}", month) for month in months)
    assert len(months) == 12
    assert {row["region"] for row in rows} == {"Toronto Region", "Rest of Canada"}
    assert {row["source"] for row in rows} == {"Direct employer", "External job board"}


def test_occupations_match_the_tech_list(rows):
    for row in rows:
        name, family = TECH_OCCUPATIONS[row["noc_code"]]
        assert (row["occupation"], row["family"]) == (name, family)


def test_levels_use_the_short_labels_and_ranks(rows):
    known = {
        "experience": {label: rank for label, rank in EXPERIENCE_LEVELS.values()},
        "education": {label: rank for label, rank in EDUCATION_LEVELS.values()},
    }
    for row in rows:
        for column, ranks in known.items():
            if row[column]:
                assert int(row[f"{column}_rank"]) == ranks[row[column]]
            else:
                assert row[f"{column}_rank"] == ""


def test_salaries_are_whole_plausible_amounts(rows):
    salaries = [int(row["annual_salary"]) for row in rows if row["annual_salary"]]
    assert len(salaries) > 0.9 * len(rows)
    # $12 an hour for 1 hour a week is the lowest plausible salary, $250 for 80 hours the highest.
    assert all(12 * 52 <= salary <= 250 * 80 * 52 for salary in salaries)


def test_rows_are_unique_per_posting_and_economic_region(rows):
    keys = [(row["posting"], row["economic_region"]) for row in rows]
    assert len(keys) == len(set(keys))
    toronto = [row for row in rows if row["region"] == "Toronto Region"]
    assert {row["economic_region"] for row in toronto} == {"Toronto Region"}
    assert "Toronto Region" not in {
        row["economic_region"] for row in rows if row["region"] == "Rest of Canada"
    }


def test_rows_of_one_posting_agree_on_what_defines_it(rows):
    # The posting key covers title, occupation, date, salary range and terms. Source,
    # requirements and weekly hours (hence the annual salary) can differ between
    # regions, which happens for a handful of the 432 postings listed in several.
    defining = ("month", "family", "noc_code", "occupation")
    other = ("source", "experience", "education", "annual_salary")
    first, differing = {}, set()
    for row in rows:
        seen = first.setdefault(row["posting"], row)
        assert all(seen[k] == row[k] for k in defining), row["posting"]
        if any(seen[k] != row[k] for k in other):
            differing.add(row["posting"])
    assert len(differing) <= 20


def test_distinct_postings_match_the_report_counts(rows):
    toronto = {row["posting"] for row in rows if row["region"] == "Toronto Region"}
    elsewhere = {row["posting"] for row in rows if row["region"] == "Rest of Canada"}
    assert len(toronto) == 5074
    assert len(toronto | elsewhere) == 11025
