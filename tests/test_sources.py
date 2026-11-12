import io
from datetime import date

import pytest

from jobmarket.sources import MonthlyFile, download, fetch_package, parse_monthly_files

TITLE = "{} Job Postings Advertised on Canada's National Job Bank Website"


def resource(title, url, language="en", fmt="CSV"):
    return {"name_translated": {"en": title}, "url": url, "language": [language], "format": fmt}


PACKAGE = {
    "result": {
        "resources": [
            resource(TITLE.format("October 2026"), "https://example.org/oct2026.csv"),
            resource(TITLE.format("October 2026"), "https://example.org/fr.csv", language="fr"),
            resource(TITLE.format("September 2026"), "https://example.org/sept2026.csv"),
            resource(TITLE.format("November 2025"), "https://example.org/november2025.csv"),
            resource("Data dictionary", "https://example.org/dictionary.csv"),
            resource(TITLE.format("August 2026"), "https://example.org/aug.xlsx", fmt="XLSX"),
        ]
    }
}


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def fake_opener(payload: bytes, calls: list):
    def opener(url, timeout):
        calls.append(url)
        return FakeResponse(payload)

    return opener


def test_parse_keeps_english_csv_months_sorted_oldest_first():
    files = parse_monthly_files(PACKAGE)
    assert [f.label for f in files] == ["2025-11", "2026-09", "2026-10"]
    assert files[-1] == MonthlyFile(date(2026, 10, 1), "https://example.org/oct2026.csv")


def test_parse_falls_back_to_plain_name_field():
    package = {
        "result": {
            "resources": [
                {
                    "name": TITLE.format("May 2026"),
                    "url": "https://example.org/may.csv",
                    "language": ["en"],
                    "format": "csv",
                }
            ]
        }
    }
    assert [f.label for f in parse_monthly_files(package)] == ["2026-05"]


def test_fetch_package_reads_json():
    calls = []
    package = fetch_package(opener=fake_opener(b'{"result": {"resources": []}}', calls))
    assert package == {"result": {"resources": []}}
    assert "package_show" in calls[0]


def test_download_writes_month_named_file(tmp_path):
    calls = []
    file = MonthlyFile(date(2026, 10, 1), "https://example.org/oct2026.csv")
    path = download(file, tmp_path / "raw", opener=fake_opener(b"data", calls))
    assert path == tmp_path / "raw" / "2026-10.csv"
    assert path.read_bytes() == b"data"
    assert not list((tmp_path / "raw").glob("*.part"))


def test_download_skips_existing_files_unless_overwrite(tmp_path):
    calls = []
    file = MonthlyFile(date(2026, 10, 1), "https://example.org/oct2026.csv")
    (tmp_path / "2026-10.csv").write_bytes(b"old")

    download(file, tmp_path, opener=fake_opener(b"new", calls))
    assert (tmp_path / "2026-10.csv").read_bytes() == b"old"
    assert calls == []

    download(file, tmp_path, overwrite=True, opener=fake_opener(b"new", calls))
    assert (tmp_path / "2026-10.csv").read_bytes() == b"new"


def test_download_refuses_plain_http(tmp_path):
    file = MonthlyFile(date(2026, 10, 1), "http://example.org/oct2026.csv")
    with pytest.raises(ValueError, match="non-HTTPS"):
        download(file, tmp_path, opener=fake_opener(b"", []))
