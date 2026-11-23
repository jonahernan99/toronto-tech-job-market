from datetime import date

from jobmarket.analysis import Table
from jobmarket.cli import EXIT_ERROR, EXIT_OK, main
from jobmarket.report import ATTRIBUTION, render_report, render_table

TABLE = Table(
    name="02_share",
    title="Share by family",
    notes="Distinct postings.",
    columns=("family", "postings", "toronto_share_pct", "median"),
    rows=[("Software", 1234, 45.678, 98500.0), ("Web | UI", 7, None, 61000.5)],
)


def test_render_table_formats_numbers_and_escapes_pipes():
    lines = render_table(TABLE).splitlines()
    assert lines[0] == "## Share by family"
    assert lines[2] == "_Distinct postings._"
    assert lines[4] == "| Family | Postings | Toronto share % | Median |"
    assert lines[5] == "| --- | ---: | ---: | ---: |"
    assert lines[6] == "| Software | 1,234 | 45.7% | 98,500 |"
    assert lines[7] == r"| Web \| UI | 7 | – | 61,000.50 |"


def test_empty_table_says_so():
    empty = Table("x", "Empty", "", ("a",), [])
    assert render_table(empty).endswith("No rows.")


def test_report_includes_every_table_and_the_licence_attribution():
    text = render_report([TABLE, TABLE], generated=date(2026, 11, 15))
    assert text.startswith("# Toronto Tech Job Market: SQL Analysis Report")
    assert "Generated on 2026-11-15" in text
    assert text.count("## Share by family") == 2
    assert ATTRIBUTION in text


def test_report_command_writes_markdown(month_files, tmp_path, capsys):
    db = tmp_path / "jobs.duckdb"
    assert main(["build", "--raw", str(month_files[0].parent), "--db", str(db)]) == EXIT_OK
    out = tmp_path / "reports" / "summary.md"
    assert main(["report", "--db", str(db), "--out", str(out)]) == EXIT_OK
    assert "Wrote 12 tables" in capsys.readouterr().out
    assert "## Overview" in out.read_text(encoding="utf-8")


def test_report_without_database_is_an_error(tmp_path, capsys):
    assert main(["report", "--db", str(tmp_path / "missing.duckdb")]) == EXIT_ERROR
    assert "run `jobmarket build` first" in capsys.readouterr().err
