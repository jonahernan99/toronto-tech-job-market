"""Drive the dashboard in headless Chrome and check every filter change applies.

Skipped when no Chrome, Chromium or Edge binary is available. CI runners have
Chrome, so the test runs there.
"""

from __future__ import annotations

import csv
import functools
import html
import http.server
import json
import os
import re
import shutil
import subprocess
import threading
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXTRACT = ROOT / "dashboard" / "data" / "tech_postings.csv"
CANDIDATES = [
    os.environ.get("CHROME_BIN", ""),
    "google-chrome",
    "google-chrome-stable",
    "chromium",
    "chromium-browser",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
]


def find_browser() -> str | None:
    for candidate in CANDIDATES:
        if candidate and (shutil.which(candidate) or Path(candidate).is_file()):
            return shutil.which(candidate) or candidate
    return None


@pytest.fixture(scope="module")
def results(tmp_path_factory):
    browser = find_browser()
    if browser is None:
        pytest.skip("no headless browser available")
    handler = functools.partial(
        type("Quiet", (http.server.SimpleHTTPRequestHandler,), {"log_message": lambda *a: None}),
        directory=str(ROOT),
    )
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        url = f"http://127.0.0.1:{server.server_port}/tests/browser/filters.html"
        profile = tmp_path_factory.mktemp("browser-profile")
        dom = subprocess.run(
            [
                browser,
                "--headless=new",
                "--disable-gpu",
                "--no-sandbox",
                f"--user-data-dir={profile}",
                "--virtual-time-budget=15000",
                "--dump-dom",
                url,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=120,
            check=True,
        ).stdout
    finally:
        server.shutdown()
    match = re.search(r'<pre id="result">(.*?)</pre>', dom, re.S)
    assert match and match.group(1) != "pending", "the dashboard did not finish loading"
    return json.loads(html.unescape(match.group(1)))


@pytest.fixture(scope="module")
def rows():
    with EXTRACT.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def expected_counts(rows, period, family, source, compare):
    """Toronto postings and comparison postings, counted independently of the page's code."""
    months = sorted({row["month"] for row in rows})[-int(period) :]
    selected = [
        row
        for row in rows
        if row["month"] in months
        and (not family or row["family"] == family)
        and (not source or row["source"] == source)
    ]
    toronto = sum(row["region"] == "Toronto Region" for row in selected)
    if compare:
        other = sum(row["economic_region"] == compare for row in selected)
    else:
        other = len({row["posting"] for row in selected if row["region"] == "Rest of Canada"})
    return toronto + other, toronto, other


def test_page_opens_with_the_filters_in_the_url(results):
    first = results[0]
    assert (first["period"], first["family"], first["source"], first["compare"]) == (
        "12",
        "Data",
        "",
        "",
    )


def test_comparison_offers_the_largest_other_regions(results, rows):
    counts = Counter(
        row["economic_region"]
        for row in rows
        if row["economic_region"] not in ("", "Toronto Region")
    )
    largest = [region for region, _ in counts.most_common(7)]
    assert results[0]["hubs"] == ["", *largest]


def test_every_filter_change_applies(results, rows):
    previous = {"period": "12", "family": "Data", "source": "", "compare": ""}
    for result in results:
        wanted = {**previous, **result["step"]}
        assert {key: result[key] for key in wanted} == wanted, result["step"]
        total, toronto, rest = expected_counts(rows, **wanted)
        assert result["status"].startswith(f"{total:,} tech postings"), result
        assert (result["toronto"], result["rest"]) == (f"{toronto:,}", f"{rest:,}"), result
        name = wanted["compare"].removesuffix(" Region") if wanted["compare"] else "Rest of Canada"
        assert result["compareName"] == name
        previous = wanted


def test_the_url_follows_the_filters(results):
    last = results[-1]
    assert last["search"] == ""
    combined = next(r for r in results if r["step"].get("family") == "IT & systems")
    assert combined["search"] == "?period=6&family=IT+%26+systems&source=Direct+employer"
