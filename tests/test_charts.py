import sys

import pytest

from jobmarket.analysis import Table
from jobmarket.charts import CHARTS, render_charts
from jobmarket.cli import EXIT_OK, main
from jobmarket.report import render_report

pytest.importorskip("matplotlib")

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

TABLES = [
    Table(
        "03_salary_by_family",
        "Salaries",
        "",
        ("family", "toronto_postings", "toronto_median", "rest_postings", "rest_of_canada_median"),
        [("Software", 10, 117500.0, 12, 92500.0), ("Data", 5, 103700.0, 4, None)],
    ),
    Table(
        "05_monthly_trend",
        "Trend",
        "",
        ("month", "toronto_postings", "canada_postings", "toronto_share_pct"),
        [("2026-09", 365, 874, 41.8), ("2026-10", 326, 836, 39.0)],
    ),
    Table(
        "06_toronto_education",
        "Education",
        "",
        ("education", "postings", "pct"),
        [("High school", 5, 20.0), ("Bachelor's degree", 20, 80.0)],
    ),
    Table("01_overview", "Overview", "", ("rows",), [(1,)]),  # no chart for this table
]


def test_every_charted_table_produces_a_png(tmp_path):
    written = render_charts(TABLES, tmp_path / "figures")
    assert set(written) == set(CHARTS)
    for path in written.values():
        assert path.read_bytes()[:8] == PNG_SIGNATURE


def test_empty_tables_are_skipped(tmp_path):
    empty = Table("05_monthly_trend", "Trend", "", ("month",), [])
    assert render_charts([empty], tmp_path) == {}


def test_report_embeds_figures_above_their_tables():
    text = render_report(TABLES, figures={"05_monthly_trend": "figures/monthly_trend.png"})
    heading = text.index("## Trend")
    image = text.index("![Trend](figures/monthly_trend.png)")
    table = text.index("| Month |")
    assert heading < image < table


def test_report_command_writes_charts(month_files, tmp_path, capsys):
    db = tmp_path / "jobs.duckdb"
    assert main(["build", "--raw", str(month_files[0].parent), "--db", str(db)]) == EXIT_OK
    out = tmp_path / "reports" / "summary.md"
    assert main(["report", "--db", str(db), "--out", str(out)]) == EXIT_OK
    # The fixture has no education data, so only the salary and trend charts are drawn.
    assert "and 2 charts" in capsys.readouterr().out
    assert (tmp_path / "reports" / "figures" / "salary_by_family.png").exists()
    assert "![" in out.read_text(encoding="utf-8")


def test_report_command_without_charts(month_files, tmp_path, capsys):
    db = tmp_path / "jobs.duckdb"
    main(["build", "--raw", str(month_files[0].parent), "--db", str(db)])
    out = tmp_path / "reports" / "summary.md"
    assert main(["report", "--db", str(db), "--out", str(out), "--no-charts"]) == EXIT_OK
    assert not (tmp_path / "reports" / "figures").exists()


def test_missing_matplotlib_only_skips_charts(month_files, tmp_path, capsys, monkeypatch):
    db = tmp_path / "jobs.duckdb"
    main(["build", "--raw", str(month_files[0].parent), "--db", str(db)])
    monkeypatch.setitem(sys.modules, "matplotlib", None)
    out = tmp_path / "reports" / "summary.md"
    assert main(["report", "--db", str(db), "--out", str(out)]) == EXIT_OK
    captured = capsys.readouterr()
    assert "skipping charts" in captured.err
    assert "and 0 charts" in captured.out
