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
