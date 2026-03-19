from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from alembic import command
from alembic.config import Config

from services.core.bootstrap import run_sample_daily_market_etl, seed_sample_reference_data
from services.db.session import SessionLocal
from workers.shared.jobs import run_daily_report_generation_job, run_indicator_update_job


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Local development management CLI")
    subparsers = parser.add_subparsers(dest="command")

    migrate_parser = subparsers.add_parser("migrate", help="Run Alembic migrations.")
    migrate_parser.add_argument("--revision", default="head")

    subparsers.add_parser("seed", help="Seed sample reference data.")

    sample_etl_parser = subparsers.add_parser("sample-etl", help="Run sample ETL data load.")
    sample_etl_parser.add_argument("--trade-date", type=date.fromisoformat, required=True)

    indicator_parser = subparsers.add_parser("indicator-update", help="Run indicator update job.")
    indicator_parser.add_argument("--trade-date", type=date.fromisoformat, required=True)

    reports_parser = subparsers.add_parser("generate-reports", help="Run daily report generation job.")
    reports_parser.add_argument("--trade-date", type=date.fromisoformat, required=True)

    args = parser.parse_args(argv)

    if args.command == "migrate":
        _run_migrations(args.revision)
        print(f"Applied migrations up to {args.revision}.")
        return 0

    if args.command == "seed":
        with SessionLocal() as session:
            seed_result = seed_sample_reference_data(session)
        print(
            "Seeded sample reference data: "
            f"instruments_created={seed_result.instruments_created}, "
            f"watchlists_created={seed_result.watchlists_created}, "
            f"tags_created={seed_result.tags_created}"
        )
        return 0

    if args.command == "sample-etl":
        with SessionLocal() as session:
            etl_result = run_sample_daily_market_etl(session, trade_date=args.trade_date)
        print(
            "Loaded sample market data: "
            f"instruments_processed={etl_result.instruments_processed}, "
            f"daily_bars_loaded={etl_result.daily_bars_loaded}"
        )
        return 0

    if args.command == "indicator-update":
        with SessionLocal() as session:
            indicator_result = run_indicator_update_job(session, args.trade_date)
        print(f"Indicator update complete: {indicator_result.metrics}")
        return 0

    if args.command == "generate-reports":
        with SessionLocal() as session:
            report_result = run_daily_report_generation_job(session, args.trade_date)
        print(f"Daily reports generated: {report_result.metrics}")
        return 0

    parser.print_help()
    return 1


def _run_migrations(revision: str) -> None:
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    command.upgrade(config, revision)


if __name__ == "__main__":
    raise SystemExit(main())
