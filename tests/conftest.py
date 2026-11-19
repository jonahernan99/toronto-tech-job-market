"""Synthetic Job Bank files in the real format: UTF-16, tab-separated, 'NA' for missing."""

from __future__ import annotations

from pathlib import Path

import pytest

from jobmarket.database import REQUIRED_COLUMNS

# The real files spell this header with two spaces, and newer months add a column.
HEADER = [
    "Economic  Region" if column == "Economic Region" else column for column in REQUIRED_COLUMNS
]
NEWER_HEADER = [*HEADER, "Official Language"]


def row(
    posting_id,
    *,
    noc="21232",
    region="Toronto Region",
    per="Hour",
    low="30",
    high="30",
    hours_per="Week",
    hours_low="37.5",
    hours_high="37.5",
    external="0",
    education="NA",
    experience="NA",
    city="Toronto",
    title="software developer",
):
    values = {
        "WIC Job Location Snapshot ID": posting_id,
        "Job Title": title,
        "NOC21 Code": noc,
        "NOC21 Code Name": "Some occupation",
        "External Indicator": external,
        "First Posting Date": "2026/10/02",
        "Vacancy Count": "1",
        "Education LOS": education,
        "Experience Level": experience,
        "NAICS": "NA",
        "Province/Territory": "Ontario",
        "City": city,
        "Economic Region": region,
        "Employment Type": "Full time",
        "Employment Term": "Permanent employment",
        "Salary Per": per,
        "Salary Minimum": low,
        "Salary Maximum": high,
        "Hours Per": hours_per,
        "Hours Minimum": hours_low,
        "Hours Maximum": hours_high,
    }
    return [values[column] for column in REQUIRED_COLUMNS]


def write_month(path: Path, rows: list[list[str]], *, newer: bool = True) -> Path:
    header = NEWER_HEADER if newer else HEADER
    lines = ["\t".join(header)]
    lines += ["\t".join([*values, "English"] if newer else values) for values in rows]
    path.write_text("\n".join(lines) + "\n", encoding="utf-16")
    return path


@pytest.fixture
def month_files(tmp_path):
    october = write_month(
        tmp_path / "2026-10.csv",
        [
            row("1"),  # 30 $/h x 37.5 h x 52 = 58,500
            row(
                "2",
                noc="64100",
                region="Ottawa Region",
                low="20",
                high="20",
                hours_per="NA",
                hours_low="NA",
                hours_high="NA",
            ),  # hourly with no stated hours: 20 $/h x 40 h x 52
            row("3", noc="21211", per="Year", low="90000", high="110000"),
            row("4", noc="21222", per="Month", low="5000", high="5000"),
            row("5", per="NA", low="NA", high="NA"),
            row("6", per="Day", low="200", high="200"),
            row("7", per="Week", low="1000", high="1000"),
            row("8", per="Bi-weekly", low="2000", high="2000", external="1"),
        ],
    )
    november = write_month(tmp_path / "2025-11.csv", [row("9", noc="21200")], newer=False)
    return [november, october]
