"""Find and download the monthly Job Bank open data files.

The dataset "Job Postings Advertised on Canada's National Job Bank Website"
publishes one CSV per month and language on open.canada.ca. File names do not
follow a fixed pattern (``oct2026``, ``sept2026``, ``july2026``...), so files
are discovered through the CKAN API and identified by their resource title,
such as "October 2026 Job Postings Advertised on Canada's National Job Bank
Website".
"""

from __future__ import annotations

import calendar
import json
import re
import shutil
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

PACKAGE_ID = "ea639e28-c0fc-48bf-b5dd-b8899bd43072"
API_URL = f"https://open.canada.ca/data/api/action/package_show?id={PACKAGE_ID}"

_MONTHS = {name.lower(): number for number, name in enumerate(calendar.month_name) if name}
_TITLE_RE = re.compile(r"^\s*(?P<month>[A-Za-z]+)\s+(?P<year>\d{4})\b")

Opener = Callable[..., Any]


@dataclass(frozen=True, order=True)
class MonthlyFile:
    """One month of English-language postings."""

    month: date
    url: str

    @property
    def label(self) -> str:
        """The month as ``YYYY-MM``, also used as the local file name."""
        return self.month.strftime("%Y-%m")


def parse_monthly_files(package: Mapping[str, Any]) -> list[MonthlyFile]:
    """Extract English CSV files from a CKAN ``package_show`` response, oldest first."""
    files: dict[date, MonthlyFile] = {}
    for resource in package["result"]["resources"]:
        if resource.get("language") != ["en"]:
            continue
        if (resource.get("format") or "").upper() != "CSV":
            continue
        title = (resource.get("name_translated") or {}).get("en") or resource.get("name") or ""
        found = _TITLE_RE.match(title)
        month_number = _MONTHS.get(found["month"].lower()) if found else None
        if month_number is None:
            continue
        month = date(int(found["year"]), month_number, 1)
        files[month] = MonthlyFile(month=month, url=resource["url"])
    return sorted(files.values())


def fetch_package(*, opener: Opener = urllib.request.urlopen, timeout: float = 60) -> dict:
    """Download the dataset's metadata from the open.canada.ca CKAN API."""
    with opener(API_URL, timeout=timeout) as response:
        return json.load(response)


def download(
    file: MonthlyFile,
    dest_dir: str | Path,
    *,
    overwrite: bool = False,
    opener: Opener = urllib.request.urlopen,
    timeout: float = 300,
) -> Path:
    """Save ``file`` as ``dest_dir/YYYY-MM.csv`` and return its path.

    Existing files are kept unless ``overwrite`` is set. Data is written to a
    temporary file first, so an interrupted download never leaves a partial
    CSV behind under the final name.
    """
    if not file.url.startswith("https://"):
        raise ValueError(f"Refusing to download from a non-HTTPS URL: {file.url}")
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    target = dest_dir / f"{file.label}.csv"
    if target.exists() and not overwrite:
        return target

    partial = target.with_suffix(".csv.part")
    with opener(file.url, timeout=timeout) as response, partial.open("wb") as out:
        shutil.copyfileobj(response, out)
    partial.replace(target)
    return target
