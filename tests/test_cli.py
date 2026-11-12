from datetime import date

import pytest

from jobmarket import cli, sources
from jobmarket.cli import EXIT_ERROR, EXIT_OK, main
from jobmarket.sources import MonthlyFile


def test_build_prints_summary(month_files, tmp_path, capsys):
    db = tmp_path / "out" / "jobs.duckdb"
    assert main(["build", "--raw", str(month_files[0].parent), "--db", str(db)]) == EXIT_OK
    out = capsys.readouterr().out
    assert "Loaded 9 postings from 2 months" in out
    assert "Tech postings: 7 in Canada, 7 in the Toronto Region" in out
    assert db.exists()


def test_build_without_files_is_an_error(tmp_path, capsys):
    assert main(["build", "--raw", str(tmp_path)]) == EXIT_ERROR
    assert "no YYYY-MM.csv files" in capsys.readouterr().err


def test_download_fetches_only_the_last_n_months(monkeypatch, tmp_path, capsys):
    months = [MonthlyFile(date(2026, m, 1), f"https://example.org/{m}.csv") for m in (8, 9, 10)]
    downloaded = []
    monkeypatch.setattr(sources, "fetch_package", lambda: {"result": {"resources": []}})
    monkeypatch.setattr(sources, "parse_monthly_files", lambda package: months)
    monkeypatch.setattr(
        sources,
        "download",
        lambda file, dest, overwrite: downloaded.append(file.label) or dest / f"{file.label}.csv",
    )

    assert main(["download", "--last", "2", "--dest", str(tmp_path)]) == EXIT_OK
    assert downloaded == ["2026-09", "2026-10"]
    assert "2026-10" in capsys.readouterr().out


def test_network_errors_are_reported(monkeypatch, capsys):
    def offline():
        raise OSError("network is unreachable")

    monkeypatch.setattr(sources, "fetch_package", offline)
    assert main(["download"]) == EXIT_ERROR
    assert "network is unreachable" in capsys.readouterr().err


def test_last_must_be_positive():
    with pytest.raises(SystemExit):
        cli.main(["download", "--last", "0"])
