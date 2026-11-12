"""Command-line interface: ``jobmarket download`` and ``jobmarket build``."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from jobmarket import sources
from jobmarket.database import build_database

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


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    handlers = {"download": _run_download, "build": _run_build}
    try:
        return handlers[args.command](args)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ERROR
