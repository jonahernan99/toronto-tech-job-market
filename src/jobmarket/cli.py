"""Command-line interface: ``jobmarket download``, ``build``, ``report`` and ``export``."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

import duckdb

from jobmarket import sources
from jobmarket.analysis import run_analysis
from jobmarket.charts import render_charts
from jobmarket.database import apply_staging, build_database
from jobmarket.export import export_postings
from jobmarket.report import render_report

EXIT_OK = 0
EXIT_ERROR = 2


def _positive_int(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return number


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="jobmarket", description="Download and analyze Job Bank open data."
    )
    commands = parser.add_subparsers(dest="command", required=True)

    download = commands.add_parser("download", help="Download the latest monthly files")
    download.add_argument(
        "--last", type=_positive_int, default=12, metavar="N", help="Most recent N months"
    )
    download.add_argument("--dest", type=Path, default=Path("data/raw"), help="Output folder")
    download.add_argument("--overwrite", action="store_true", help="Download existing files again")

    build = commands.add_parser("build", help="Load downloaded files into DuckDB")
    build.add_argument("--raw", type=Path, default=Path("data/raw"), help="Folder of YYYY-MM.csv")
    build.add_argument("--db", type=Path, default=Path("data/jobmarket.duckdb"), help="Database")

    report = commands.add_parser("report", help="Run the SQL analysis and write a Markdown report")
    report.add_argument("--db", type=Path, default=Path("data/jobmarket.duckdb"), help="Database")
    report.add_argument("--out", type=Path, default=Path("reports/summary.md"), help="Report file")
    report.add_argument("--no-charts", action="store_true", help="Skip the PNG charts")

    export = commands.add_parser("export", help="Write one CSV row per tech posting")
    export.add_argument("--db", type=Path, default=Path("data/jobmarket.duckdb"), help="Database")
    export.add_argument(
        "--out", type=Path, default=Path("dashboard/data/tech_postings.csv"), help="CSV file"
    )
    return parser


def _run_download(args: argparse.Namespace) -> int:
    files = sources.parse_monthly_files(sources.fetch_package())[-args.last :]
    for file in files:
        path = sources.download(file, args.dest, overwrite=args.overwrite)
        print(f"{file.label}  {path}")
    return EXIT_OK


def _run_build(args: argparse.Namespace) -> int:
    files = sorted(args.raw.glob("[0-9][0-9][0-9][0-9]-[0-9][0-9].csv"))
    if not files:
        print(f"error: no YYYY-MM.csv files in {args.raw}", file=sys.stderr)
        return EXIT_ERROR
    args.db.parent.mkdir(parents=True, exist_ok=True)
    con = build_database(files, args.db)
    rows, months, tech, toronto_tech = con.sql(
        """
        select count(*), count(distinct source_month),
               count(*) filter (where is_tech),
               count(*) filter (where is_tech and is_toronto)
        from postings
        """
    ).fetchall()[0]
    con.close()
    print(f"Loaded {rows:,} postings from {months} months into {args.db}")
    print(f"Tech postings: {tech:,} in Canada, {toronto_tech:,} in the Toronto Region")
    return EXIT_OK


def _run_report(args: argparse.Namespace) -> int:
    if not args.db.exists():
        print(f"error: {args.db} not found; run `jobmarket build` first", file=sys.stderr)
        return EXIT_ERROR
    con = duckdb.connect(str(args.db))
    try:
        apply_staging(con)
        tables = run_analysis(con)
    finally:
        con.close()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    figures: dict[str, str] = {}
    if not args.no_charts:
        try:
            written = render_charts(tables, args.out.parent / "figures")
        except ImportError:
            print("warning: matplotlib is not installed, skipping charts", file=sys.stderr)
        else:
            figures = {name: f"figures/{path.name}" for name, path in written.items()}
    args.out.write_text(render_report(tables, figures=figures), encoding="utf-8")
    print(f"Wrote {len(tables)} tables and {len(figures)} charts to {args.out}")
    return EXIT_OK


def _run_export(args: argparse.Namespace) -> int:
    if not args.db.exists():
        print(f"error: {args.db} not found; run `jobmarket build` first", file=sys.stderr)
        return EXIT_ERROR
    con = duckdb.connect(str(args.db))
    try:
        apply_staging(con)
        rows = export_postings(con, args.out)
    finally:
        con.close()
    print(f"Wrote {rows:,} tech postings to {args.out}")
    return EXIT_OK


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    handlers = {
        "download": _run_download,
        "build": _run_build,
        "report": _run_report,
        "export": _run_export,
    }
    try:
        return handlers[args.command](args)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ERROR
