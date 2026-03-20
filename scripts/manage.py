from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from alembic import command
from alembic.config import Config

from services.core.bootstrap import (
    DEFAULT_DEMO_TRADE_DATE,
    DEFAULT_V1_UNIVERSE_PRESET,
    generate_demo_data,
    load_instrument_universe,
    run_sample_daily_market_etl,
    seed_sample_reference_data,
)
from services.core.smoke import run_smoke_test
from services.db.session import SessionLocal
from workers.shared.jobs import run_daily_report_generation_job, run_indicator_update_job
from config.universe import describe_universe_preset, list_available_universe_presets


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Local development management CLI")
    subparsers = parser.add_subparsers(dest="command")

    migrate_parser = subparsers.add_parser("migrate", help="Run Alembic migrations.")
    migrate_parser.add_argument("--revision", default="head")

    subparsers.add_parser("seed", help="Seed sample reference data.")

    subparsers.add_parser("list-universes", help="List available universe presets.")

    universe_parser = subparsers.add_parser("load-universe", help="Load a broader instrument universe preset.")
    universe_parser.add_argument("--preset", default=DEFAULT_V1_UNIVERSE_PRESET)
    universe_parser.add_argument(
        "--scope",
        action="append",
        default=[],
        help="Limit loading to one or more scope keys declared by the preset.",
    )
    universe_parser.add_argument(
        "--skip-watchlists",
        action="store_true",
        help="Load instruments and tags without preset watchlists.",
    )

    demo_data_parser = subparsers.add_parser("demo-data", help="Generate frontend-visible local demo data.")
    demo_data_parser.add_argument("--trade-date", type=date.fromisoformat, default=DEFAULT_DEMO_TRADE_DATE)

    sample_etl_parser = subparsers.add_parser("sample-etl", help="Run sample ETL data load.")
    sample_etl_parser.add_argument("--trade-date", type=date.fromisoformat, required=True)

    indicator_parser = subparsers.add_parser("indicator-update", help="Run indicator update job.")
    indicator_parser.add_argument("--trade-date", type=date.fromisoformat, required=True)

    reports_parser = subparsers.add_parser("generate-reports", help="Run daily report generation job.")
    reports_parser.add_argument("--trade-date", type=date.fromisoformat, required=True)

    smoke_parser = subparsers.add_parser("smoke-test", help="Run local startup smoke checks.")
    smoke_parser.add_argument("--api-base-url", default="http://localhost:8000")

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

    if args.command == "list-universes":
        for preset_name in list_available_universe_presets():
            description = describe_universe_preset(preset_name)
            scope_keys = description["scope_keys"]
            scope_text = ",".join(scope_keys if isinstance(scope_keys, list) else []) or "all"
            print(
                f"{preset_name}: instruments={description['instrument_count']}, "
                f"watchlists={description['watchlist_count']}, scopes={scope_text}"
            )
        return 0

    if args.command == "load-universe":
        with SessionLocal() as session:
            result = load_instrument_universe(
                session,
                preset_name=args.preset,
                include_watchlists=not args.skip_watchlists,
                scope_keys=tuple(args.scope),
            )
        print(
            "Loaded instrument universe: "
            f"preset={result.preset_name}, "
            f"requested_scopes={','.join(result.requested_scope_keys) or 'all'}, "
            f"scopes_declared={result.scopes_declared}, "
            f"instruments_created={result.instruments_created}, "
            f"instruments_updated={result.instruments_updated}, "
            f"tags_created={result.tags_created}, "
            f"watchlists_created={result.watchlists_created}, "
            f"watchlist_items_added={result.watchlist_items_added}, "
            f"total_instruments={result.total_instruments}"
        )
        return 0

    if args.command == "demo-data":
        with SessionLocal() as session:
            demo_result = generate_demo_data(session, trade_date=args.trade_date)
        print(
            "Generated demo data: "
            f"trade_date={demo_result.trade_date.isoformat()}, "
            f"daily_bars_loaded={demo_result.daily_bars_loaded}, "
            f"indicator_values_persisted={demo_result.indicator_values_persisted}, "
            f"tw_derivatives_features_persisted={demo_result.tw_derivatives_features_persisted}, "
            f"candidate_items_created={demo_result.candidate_items_created}, "
            f"backtest_trades_created={demo_result.backtest_trades_created}, "
            f"reports_persisted={demo_result.reports_persisted}"
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

    if args.command == "smoke-test":
        with SessionLocal() as session:
            smoke_result = run_smoke_test(session, api_base_url=args.api_base_url)
        print(
            "Smoke test result: "
            f"database_connectivity_ok={smoke_result.database_connectivity_ok}, "
            f"api_health_ok={smoke_result.api_health_ok}, "
            f"schema_reachable={smoke_result.schema_reachable}, "
            f"sample_data_ok={smoke_result.sample_data_ok}, "
            f"checked_symbols={','.join(smoke_result.checked_symbols)}"
        )
        return 0 if smoke_result.passed else 1

    parser.print_help()
    return 1


def _run_migrations(revision: str) -> None:
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    command.upgrade(config, revision)


if __name__ == "__main__":
    raise SystemExit(main())
